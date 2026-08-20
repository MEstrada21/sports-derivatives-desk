"""AMENDMENT 1 / A1 — measurement-gap residual test (corn x Jul10-Aug31 difference-in-differences).

Run under AMENDMENT_1_measurement_gap.md (sha256 fb43b481...). EXPLORATORY, not pre-registered:
the parent data pull had already happened. Sign predictions were committed in the amendment BEFORE
these fits:

    break    NEGATIVE   (thinner-than-measured air -> less Magnus, and via grip less spin)
    spin     NEGATIVE   (confirmatory: understated humidity -> understated grip effect)
    HR/BIP   POSITIVE   (the operator's carry channel)
    velocity ZERO       (PLACEBO -- responds to neither density channel in the parent study;
                         a hit here means roster/composition confound, not air)

Park FE absorb the corn main effect, season x month FE absorb the window main effect, so the
interaction is a clean DiD. Everything the parent spec controlled is still controlled, so this asks:
does corn-belt late summer carry signal AFTER we have used all the weather we actually measured?
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

from analyze import (SEED, OUT, load, absorb, dummies, wls_cluster, GAME_COLS,
                     permute_within, stage1b)

WIN_LO, WIN_HI = 191, 243          # Jul 10 - Aug 31
VAPOR_SLOPE_IN_PER_KGM3 = -39.06   # parent study, break vs vapour-density channel


def add_cell(d):
    d = d.copy()
    d["corn_window"] = (d.is_corn & d.doy.between(WIN_LO, WIN_HI)).astype(float)
    return d


def pitch_did(cells, games, mask, y_col, label, rng=None):
    g = games[mask]
    d = cells.merge(g[GAME_COLS + ["is_corn", "doy"]], on="game_id", how="inner")
    d = d[d.n >= 3].dropna(subset=["break_mag", "velo", "spin"]).copy()
    if rng is not None:
        d = permute_within(d, games, rng)
    d = add_cell(d)
    d["fe"] = d.pitcher_id + "|" + d.pitch_type.astype(str) + "|" + d.season
    reg = pd.DataFrame({"corn_window": d.corn_window.values,
                        "rho_dry": d.rho_dry.values,
                        "vapor_deficit": d.vapor_density_deficit.values,
                        "temp": d.temperature_2m_c.values,
                        "temp2": d.temperature_2m_c.values ** 2,
                        "wind": d.wind_speed_10m_ms.values,
                        "precip": d.precipitation_mm.values})
    X = pd.concat([reg, dummies(d.park_id).reset_index(drop=True),
                   dummies(d.season_month).reset_index(drop=True)], axis=1)
    cols = list(X.columns)
    frame = pd.concat([pd.DataFrame({y_col: d[y_col].values, "fe": d.fe.values, "n": d.n.values}),
                       X], axis=1)
    dm = absorb(frame, [y_col] + cols, "fe", "n")
    res, _, _ = wls_cluster(dm[y_col].values, dm[cols].values, d.n.values, d.game_id.values, cols)
    b, se = res["corn_window"]
    return {"label": label, "y": y_col, "beta": b, "se": se, "z": b / se,
            "ci_lo": b - 1.96 * se, "ci_hi": b + 1.96 * se,
            "n_pitches": int(d.n.sum()),
            "n_cell_pitches": int(d[d.corn_window > 0].n.sum())}


def game_did(games, mask, y_num, y_den, label):
    g = add_cell(games[mask])
    g = g[(g[y_den] > 0) & (~g.is_coors)]
    y = g[y_num].values / g[y_den].values
    reg = pd.DataFrame({"corn_window": g.corn_window.values,
                        "dew": g.dew_point_c.values,
                        "temp": g.temperature_2m_c.values,
                        "temp2": g.temperature_2m_c.values ** 2,
                        "wind": g.wind_speed_10m_ms.values,
                        "precip": g.precipitation_mm.values, "const": 1.0})
    X = pd.concat([reg, dummies(g.park_id).reset_index(drop=True),
                   dummies(g.season_month).reset_index(drop=True)], axis=1)
    res, _, _ = wls_cluster(y, X.values, g[y_den].values, g.game_id.values, list(X.columns))
    b, se = res["corn_window"]
    return {"label": label, "y": f"{y_num}/{y_den}", "beta_pp": 100 * b, "se_pp": 100 * se,
            "z": b / se, "ci_lo_pp": 100 * (b - 1.96 * se), "ci_hi_pp": 100 * (b + 1.96 * se),
            "n_games": int(len(g)), "n_cell_games": int((g.corn_window > 0).sum())}


def main():
    games, cells = load()
    open_mask = ((~games.is_roofed) & (~games.is_coors)).values
    R = {"seed": SEED, "amendment": "AMENDMENT_1_measurement_gap.md",
         "status": "EXPLORATORY - not pre-registered, parent data pull preceded it",
         "window_doy": [WIN_LO, WIN_HI]}

    print("== A1: corn x Jul10-Aug31 difference-in-differences ==")
    print("   signs committed in the amendment BEFORE these fits:")
    print("   break NEGATIVE | spin NEGATIVE | HR POSITIVE | velocity ZERO (placebo)\n")

    preds = {"break_mag": "NEGATIVE", "spin": "NEGATIVE", "velo": "ZERO (placebo)"}
    for y in ("break_mag", "spin", "velo"):
        r = pitch_did(cells, games, open_mask, y, f"corn x window -> {y}")
        R[f"pitch_{y}"] = r
        got = "NEG" if r["z"] < -1.96 else ("POS" if r["z"] > 1.96 else "ZERO")
        print(f"  {y:10s} beta={r['beta']:+10.4f}  se={r['se']:9.4f}  z={r['z']:+6.2f}  "
              f"95%CI=[{r['ci_lo']:+.4f},{r['ci_hi']:+.4f}]  predicted {preds[y]:14s} got {got}"
              f"   (cell n={r['n_cell_pitches']:,} pitches)")

    print()
    for nm, yn, yd in (("HR/BIP", "hr", "bip"), ("K/PA", "k", "pa")):
        r = game_did(games, open_mask, yn, yd, f"corn x window -> {nm}")
        R[f"game_{yn}"] = r
        print(f"  {nm:10s} beta={r['beta_pp']:+10.4f} pp  se={r['se_pp']:8.4f}  z={r['z']:+6.2f}  "
              f"95%CI=[{r['ci_lo_pp']:+.4f},{r['ci_hi_pp']:+.4f}]"
              f"   (cell n={r['n_cell_games']} games)")

    print("\n== permutation null on the DiD cell (weather shuffled within park x month) ==")
    perm = [pitch_did(cells, games, open_mask, "break_mag", "perm",
                      rng=np.random.default_rng(SEED + 500 + i))["z"] for i in range(5)]
    R["perm_break_z"] = perm
    print(f"  break DiD z under 5 weather permutations: "
          f"{', '.join(f'{v:+.2f}' for v in perm)}")
    print("  (NOTE: permuting weather does NOT move the corn x window indicator -- this checks that")
    print("   the DiD cell is not an artifact of the weather controls, not that the cell is null.)")

    print("\n== implied humidity understatement (the operator's question, in his units) ==")
    b = R["pitch_break_mag"]["beta"]
    lo, hi = R["pitch_break_mag"]["ci_lo"], R["pitch_break_mag"]["ci_hi"]
    def to_kgm3(x):
        return x / VAPOR_SLOPE_IN_PER_KGM3
    g = games[open_mask]
    cell = add_cell(g)
    cell = cell[cell.corn_window > 0]
    t_mean = float(cell.temperature_2m_c.mean())
    p_mean = float(cell.surface_pressure_hpa.mean())
    d_mean = float(cell.dew_point_c.mean())

    def dew_for_extra_vapor(extra_kgm3):
        """How much extra dew point would produce `extra_kgm3` more vapour density deficit."""
        from build_weather import air_density, dew_point_c, sat_vapor_hpa
        lo_d, hi_d = d_mean - 15, d_mean + 15
        target = extra_kgm3
        for _ in range(60):
            mid = (lo_d + hi_d) / 2
            e_mid = sat_vapor_hpa(np.array([mid]))[0]
            e_base = sat_vapor_hpa(np.array([d_mean]))[0]
            rho_mid = (((p_mean - e_mid) * 100 * 0.0289652 + e_mid * 100 * 0.018016)
                       / (8.31446 * (t_mean + 273.15)))
            rho_base = (((p_mean - e_base) * 100 * 0.0289652 + e_base * 100 * 0.018016)
                        / (8.31446 * (t_mean + 273.15)))
            got = rho_base - rho_mid
            if got < target:
                lo_d = mid
            else:
                hi_d = mid
        return (lo_d + hi_d) / 2 - d_mean

    kg = to_kgm3(b)
    R["implied"] = {"break_beta_in": b, "implied_extra_vapor_kgm3": kg,
                    "implied_extra_dewpoint_c": float(dew_for_extra_vapor(kg)) if kg > 0 else
                    -float(dew_for_extra_vapor(-kg)),
                    "cell_mean_temp_c": t_mean, "cell_mean_dew_c": d_mean,
                    "ci_kgm3": [to_kgm3(hi), to_kgm3(lo)]}
    print(f"  cell mean: {t_mean:.1f} C, dew {d_mean:.1f} C, {p_mean:.0f} hPa")
    print(f"  break DiD {b:+.4f} in -> implied extra vapour density {kg:+.6f} kg/m3"
          f" -> implied extra dew point {R['implied']['implied_extra_dewpoint_c']:+.2f} C")
    print(f"  (Stage-2 measured a +1.02 C corn anomaly ALREADY VISIBLE in the station data;"
          f" this is the part the station allegedly MISSES)")

    json.dump(R, open(os.path.join(OUT, "measurement_gap.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'measurement_gap.json')}")


if __name__ == "__main__":
    main()
