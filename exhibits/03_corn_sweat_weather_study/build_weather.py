"""Stage 0: game-level air-density / dew-point table. Weather + schedule only, NO outcomes.

Idempotent: writes out/game_weather.parquet, skips if present unless --force.
"""
from __future__ import annotations
import argparse, glob, json, os
import numpy as np
import pandas as pd

LANE = os.path.dirname(os.path.abspath(__file__))
# DATA_ROOT must contain data/weather/{hourly,game_index,venue_meta.json} built from
# public sources (Open-Meteo ERA5 hourly at park coordinates; MLB StatsAPI schedule).
# Default: a data/ tree placed (or symlinked) next to these scripts.
ROOT = os.environ.get("DATA_ROOT", LANE)
OUT = os.path.join(LANE, "out")

M_D, M_V, R_GAS = 0.0289652, 0.018016, 8.31446

# operator's corn-belt list
CORN_TEAMS = {"STL", "CHC", "CWS", "CIN", "DET", "MIL", "KC", "MIN"}
CORN_PARKS = {  # park_id -> team
    "2889": "STL", "17": "CHC", "4": "CWS", "2602": "CIN",
    "2394": "DET", "32": "MIL", "7": "KC", "3312": "MIN",
}
COORS = "19"


def sat_vapor_hpa(t_c: np.ndarray) -> np.ndarray:
    """Alduchov-Eskridge Magnus saturation vapour pressure, hPa."""
    return 6.1094 * np.exp(17.625 * t_c / (t_c + 243.04))


def dew_point_c(t_c: np.ndarray, rh_pct: np.ndarray) -> np.ndarray:
    rh = np.clip(rh_pct, 1.0, 100.0) / 100.0
    g = np.log(rh) + 17.625 * t_c / (243.04 + t_c)
    return 243.04 * g / (17.625 - g)


def air_density(t_c: np.ndarray, rh_pct: np.ndarray, p_hpa: np.ndarray) -> np.ndarray:
    p_v = (np.clip(rh_pct, 0.0, 100.0) / 100.0) * sat_vapor_hpa(t_c)
    p_d = p_hpa - p_v
    return (p_d * 100.0 * M_D + p_v * 100.0 * M_V) / (R_GAS * (t_c + 273.15))


def load_hourly() -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(ROOT, "data/weather/hourly/**/*.parquet"), recursive=True))
    cols = ["park_id", "ts_utc", "temperature_2m_c", "relative_humidity_2m_pct",
            "surface_pressure_hpa", "wind_speed_10m_ms", "wind_direction_10m_deg",
            "precipitation_mm", "grid_elevation_m"]
    df = pd.concat([pd.read_parquet(f, columns=cols) for f in files], ignore_index=True)
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True, format="ISO8601")
    df["park_id"] = df["park_id"].astype(str)
    # dedupe on (park, hour) keeping last write
    df = df.sort_values("ts_utc").drop_duplicates(["park_id", "ts_utc"], keep="last")
    return df


def load_games() -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(ROOT, "data/weather/game_index/*.parquet")))
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df["park_id"] = df["park_id"].astype(str)
    df["game_id"] = df["game_id"].astype(str)
    df = df.sort_values("receipt_time_utc").drop_duplicates("game_id", keep="last")
    df["first_pitch_utc"] = pd.to_datetime(df["first_pitch_utc"], utc=True, format="ISO8601")
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    dest = os.path.join(OUT, "game_weather.parquet")
    if os.path.exists(dest) and not args.force:
        print(f"SKIP (exists): {dest}")
        return

    venues = json.load(open(os.path.join(ROOT, "data/weather/venue_meta.json")))["venues"]
    games = load_games()

    # --- regular-season / MLB-venue filter (archive contains spring + exhibition) ---
    park_counts = games.groupby("park_id").size()
    mlb_parks = set(park_counts[park_counts > 100].index)
    games = games[games.park_id.isin(mlb_parks)].copy()
    games["md"] = games.game_date.str[5:]
    n_pre = len(games)
    games = games[games.md >= "03-20"].copy()
    print(f"venue+date filter: {n_pre} -> {len(games)} games ({len(mlb_parks)} MLB parks)")

    hourly = load_hourly()
    hourly["hour"] = hourly.ts_utc.dt.floor("h")
    games["hour"] = games.first_pitch_utc.dt.floor("h")

    m = games.merge(hourly.drop(columns=["ts_utc"]), on=["park_id", "hour"], how="left",
                    validate="many_to_one")
    print(f"weather join: {m.temperature_2m_c.notna().mean():.4f} matched")
    m = m[m.temperature_2m_c.notna()].copy()

    t, rh, p = m.temperature_2m_c.values, m.relative_humidity_2m_pct.values, m.surface_pressure_hpa.values
    m["dew_point_c"] = dew_point_c(t, rh)
    m["rho"] = air_density(t, rh, p)
    # counterfactual densities isolating each channel, held at park-season means of the other
    m["rho_dry"] = air_density(t, np.zeros_like(rh), p)          # same T,P, zero vapour
    m["vapor_density_deficit"] = m["rho_dry"] - m["rho"]          # kg/m3 removed by water vapour
    m["temp_f"] = t * 9 / 5 + 32
    m["dew_point_f"] = m.dew_point_c * 9 / 5 + 32

    m["roof"] = m.park_id.map(lambda k: venues.get(k, {}).get("roof", "Unknown"))
    m["elev_ft"] = m.park_id.map(lambda k: venues.get(k, {}).get("elevation_ft"))
    m["park_name"] = m.park_id.map(lambda k: venues.get(k, {}).get("name"))
    m["state"] = m.park_id.map(lambda k: venues.get(k, {}).get("state"))
    m["lat"] = m.park_id.map(lambda k: venues.get(k, {}).get("lat"))
    m["is_roofed"] = m.roof.isin(["Retractable", "Dome"])
    m["is_corn"] = m.park_id.isin(CORN_PARKS)
    m["corn_team"] = m.park_id.map(CORN_PARKS)
    m["is_coors"] = m.park_id.eq(COORS)
    m["season"] = m.game_date.str[:4]
    m["month"] = m.game_date.str[5:7]
    m["doy"] = pd.to_datetime(m.game_date).dt.dayofyear

    keep = ["game_id", "game_date", "season", "month", "doy", "park_id", "park_name", "state",
            "lat", "elev_ft", "roof", "is_roofed", "is_corn", "corn_team", "is_coors",
            "first_pitch_utc", "n_pa", "temperature_2m_c", "temp_f", "relative_humidity_2m_pct",
            "surface_pressure_hpa", "dew_point_c", "dew_point_f", "rho", "rho_dry",
            "vapor_density_deficit", "wind_speed_10m_ms", "wind_direction_10m_deg",
            "precipitation_mm", "grid_elevation_m"]
    m[keep].to_parquet(dest, index=False)
    print(f"WROTE {dest}  rows={len(m)}")

    # --- power input: residual SD of dew point after temp + park x month ---
    sub = m[~m.is_coors]
    y = sub.dew_point_c.values
    X = pd.get_dummies(sub.park_id.astype(str) + "_" + sub.month.astype(str), drop_first=True).values.astype(float)
    X = np.column_stack([np.ones(len(sub)), sub.temperature_2m_c.values,
                         sub.temperature_2m_c.values ** 2, X])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    stats = {
        "n_games": int(len(m)),
        "n_parks": int(m.park_id.nunique()),
        "dew_sd_raw_c": float(np.std(m.dew_point_c)),
        "dew_sd_resid_after_temp_parkmonth_c": float(np.std(resid)),
        "rho_sd_raw": float(np.std(m.rho)),
        "rho_sd_ex_coors": float(np.std(m[~m.is_coors].rho)),
        "vapor_deficit_sd": float(np.std(m.vapor_density_deficit)),
        "vapor_deficit_mean": float(np.mean(m.vapor_density_deficit)),
        "n_roofed_games": int(m.is_roofed.sum()),
        "n_corn_games": int(m.is_corn.sum()),
    }
    json.dump(stats, open(os.path.join(OUT, "weather_stats.json"), "w"), indent=2)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
