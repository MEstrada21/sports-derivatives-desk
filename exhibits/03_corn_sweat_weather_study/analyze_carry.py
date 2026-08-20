"""AMENDMENT 2 — carry distance as a continuous air-density readout.

Pre-registered in AMENDMENT_2_statcast_carry.md (sha256 f1be4880...), frozen BEFORE the pull.

PRIMARY (H2-1): the equal-and-opposite test on CARRY.
  A struck ball has no grip channel -- once EV and LA are conditioned on, nothing the pitcher's
  hand did can change how far it flies. So where the break instrument REJECTED equal-and-opposite
  (vapour 3.3x oversized, z=-8.2), carry should PASS.

  distance falls with density:   beta(rho_dry) < 0,  beta(vapor_deficit) > 0,  sum ~ 0
  physics magnitude: ~2.5 ft per 1% of density on a 400-ft fly  ->  ~215 ft per kg/m3

TRAP GUARDED: Statcast populates launch_speed / launch_angle / hit_distance_sc for FOUL balls too
(they have no bb_type and no event). Fouls are not balls in play and their distance is not carry.
The in-play filter is bb_type non-null, and the foul contamination rate is reported, not assumed.
"""
from __future__ import annotations
import argparse, glob, json, os
import numpy as np
import pandas as pd

from analyze import SEED, OUT, load, absorb, dummies, wls_cluster, linear_combo

LANE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(LANE, "cache", "statcast")

LA_LO, LA_HI = 10.0, 50.0
EV_MIN, DIST_MIN = 60.0, 50.0
EV_BIN, LA_BIN = 3.0, 3.0
PHYSICS_FT_PER_KGM3 = 215.0     # 2.5 ft per 1% density at rho~1.16
WIN_LO, WIN_HI = 191, 243


def load_statcast(verbose=True):
    files = sorted(glob.glob(os.path.join(CACHE, "*.parquet")))
    parts = []
    for f in files:
        try:
            d = pd.read_parquet(f)
        except Exception:
            continue
        if len(d):
            parts.append(d)
    raw = pd.concat(parts, ignore_index=True)
    n0 = len(raw)
    raw["game_id"] = raw.game_pk.astype(str)
    steps = {"cached_batted_rows": n0}

    r = raw[raw.game_type.astype(str) == "R"]
    steps["after_game_type_R"] = len(r)
    # FOUL GUARD: fouls carry launch data but no bb_type / no in-play event
    foul_rate = float(r.bb_type.isna().mean())
    r = r[r.bb_type.notna()]
    steps["after_in_play_bb_type"] = len(r)
    steps["foul_or_nonBIP_fraction_dropped"] = foul_rate
    r = r[(r.launch_angle >= LA_LO) & (r.launch_angle <= LA_HI)]
    steps["after_launch_angle_window"] = len(r)
    r = r[(r.launch_speed >= EV_MIN) & (r.hit_distance_sc > DIST_MIN)]
    steps["after_ev_dist_floor"] = len(r)
    if verbose:
        print("  filter cascade:")
        for k, v in steps.items():
            print(f"    {k:38s} {v:,}" if isinstance(v, int) else f"    {k:38s} {v:.4f}")
    return r.copy(), steps


def build(verbose=True):
    games, _ = load()
    sc, steps = load_statcast(verbose)
    g = games[["game_id", "park_id", "season", "season_month", "doy", "is_corn", "is_coors",
               "is_roofed", "rho", "rho_dry", "vapor_density_deficit", "temperature_2m_c",
               "dew_point_c", "surface_pressure_hpa", "wind_speed_10m_ms",
               "wind_direction_10m_deg", "precipitation_mm"]]
    d = sc.merge(g, on="game_id", how="inner")
    steps["after_weather_join"] = len(d)
    steps["weather_join_rate"] = float(len(d) / max(len(sc), 1))
    if verbose:
        print(f"    {'after_weather_join':38s} {len(d):,}  "
              f"(join rate {steps['weather_join_rate']:.4f})")
    d["ev_cell"] = (np.floor(d.launch_speed / EV_BIN).astype(int).astype(str) + "_" +
                    np.floor(d.launch_angle / LA_BIN).astype(int).astype(str))
    th = np.deg2rad(d.wind_direction_10m_deg.values)
    d["wind_sin"] = d.wind_speed_10m_ms.values * np.sin(th)
    d["wind_cos"] = d.wind_speed_10m_ms.values * np.cos(th)
    return d, steps


def fit(d, y="hit_distance_sc", label="", planted=0.0, rng=None, extra_cell=None,
        park_wind=True, temp_ctrl="quad"):
    d = d.copy()
    if rng is not None:
        wcols = ["rho", "rho_dry", "vapor_density_deficit", "temperature_2m_c", "dew_point_c",
                 "wind_sin", "wind_cos", "wind_speed_10m_ms"]
        gm = d[["game_id", "park_id"] + wcols].drop_duplicates("game_id").copy()
        gm["mo"] = gm.game_id.map(d.set_index("game_id").season_month.to_dict())
        parts = []
        for _, blk in gm.groupby(["park_id", "mo"], sort=True):
            b = blk.copy()
            b[wcols] = b[wcols].values[rng.permutation(len(b))]
            parts.append(b)
        sh = pd.concat(parts, ignore_index=True)[["game_id"] + wcols]
        d = d.drop(columns=wcols).merge(sh, on="game_id", how="inner")
    if planted:
        d[y] = d[y] + planted * (d.vapor_density_deficit - d.vapor_density_deficit.mean())

    base = {"rho_dry": d.rho_dry.values, "vapor_deficit": d.vapor_density_deficit.values,
            "precip": d.precipitation_mm.values}
    if temp_ctrl == "quad":
        base["temp"] = d.temperature_2m_c.values
        base["temp2"] = d.temperature_2m_c.values ** 2
    if extra_cell is not None:
        base["corn_window"] = extra_cell
    blocks = [pd.DataFrame(base)]
    if temp_ctrl == "bins":
        tb = pd.cut(d.temperature_2m_c, bins=np.arange(-5, 46, 1)).astype(str)
        blocks.append(dummies(tb).reset_index(drop=True))
    if park_wind:
        for nm in ("wind_sin", "wind_cos"):
            w = pd.get_dummies(d.park_id.astype(str), prefix=f"w{nm}").astype(float)
            w = w.mul(d[nm].values, axis=0)
            blocks.append(w.reset_index(drop=True))
    else:
        blocks[0]["wind_sin"] = d.wind_sin.values
        blocks[0]["wind_cos"] = d.wind_cos.values
    blocks += [dummies(d.park_id).reset_index(drop=True),
               dummies(d.season_month).reset_index(drop=True)]
    X = pd.concat([b.reset_index(drop=True) for b in blocks], axis=1)
    X = X.loc[:, X.std(numeric_only=True) > 0]
    cols = list(X.columns)
    frame = pd.concat([pd.DataFrame({y: d[y].values, "cell": d.ev_cell.values,
                                     "w": 1.0}), X], axis=1)
    dm = absorb(frame, [y] + cols, "cell", "w")
    res, beta, V = wls_cluster(dm[y].values, dm[cols].values, np.ones(len(d)),
                               d.game_id.values, cols)
    s, se, z = linear_combo(beta, V, cols, {"rho_dry": 1.0, "vapor_deficit": 1.0})
    out = {"label": label, "y": y, "n": int(len(d)), "n_games": int(d.game_id.nunique()),
           "n_cells": int(d.ev_cell.nunique()),
           "beta_pressure": res["rho_dry"][0], "se_pressure": res["rho_dry"][1],
           "z_pressure": res["rho_dry"][0] / res["rho_dry"][1],
           "beta_vapor": res["vapor_deficit"][0], "se_vapor": res["vapor_deficit"][1],
           "z_vapor": res["vapor_deficit"][0] / res["vapor_deficit"][1],
           "sum_equal_and_opposite": s, "se_sum": se, "z_equal_and_opposite": z,
           "mean_y": float(d[y].mean())}
    if extra_cell is not None:
        out["beta_corn_window"] = res["corn_window"][0]
        out["se_corn_window"] = res["corn_window"][1]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perm", type=int, default=200)
    args = ap.parse_args()

    print("== AMENDMENT 2: carry distance vs air density ==\n")
    d, steps = build()
    R = {"seed": SEED, "amendment": "AMENDMENT_2_statcast_carry.md",
         "amendment_sha256": "f1be4880a47ee1d2822489fc1b3f6fb7c3d0c61c8d796467028a13e84cbfddd7",
         "status": "PRE-REGISTERED (data ask registered in parent prereg before results;"
                   " spec frozen before pull)",
         "filters": steps, "physics_ft_per_kgm3": PHYSICS_FT_PER_KGM3}

    prim = d[(~d.is_coors) & (~d.is_roofed)]
    print(f"\n  primary sample: {len(prim):,} batted balls, {prim.game_id.nunique():,} games, "
          f"mean distance {prim.hit_distance_sc.mean():.1f} ft\n")

    print("== H2-1 PRIMARY: equal-and-opposite on CARRY "
          f"(physics: pressure ~{-PHYSICS_FT_PER_KGM3:.0f}, vapour ~{PHYSICS_FT_PER_KGM3:+.0f}) ==")
    R["h2_1_primary"] = fit(prim, label="PRIMARY open-air ex-Coors")
    r = R["h2_1_primary"]
    print(f"  pressure channel {r['beta_pressure']:+9.1f} ft per kg/m3 (se {r['se_pressure']:6.1f},"
          f" z={r['z_pressure']:+6.2f})")
    print(f"  vapour   channel {r['beta_vapor']:+9.1f} ft per kg/m3 (se {r['se_vapor']:6.1f},"
          f" z={r['z_vapor']:+6.2f})")
    print(f"  EQUAL-AND-OPPOSITE: sum={r['sum_equal_and_opposite']:+.1f} "
          f"(se {r['se_sum']:.1f}) z={r['z_equal_and_opposite']:+.2f}  -> "
          f"{'PASSES (cannot reject)' if abs(r['z_equal_and_opposite'])<1.96 else 'REJECTS'}")
    print(f"  [break instrument REJECTED this at z=-8.2; carry has no grip channel]\n")

    print("== controls ==")
    R["h2_placebo_roofed"] = fit(d[d.is_roofed], label="roofed placebo (vapour channel only)")
    r = R["h2_placebo_roofed"]
    print(f"  roofed placebo   vapour {r['beta_vapor']:+9.1f} (z={r['z_vapor']:+6.2f})   "
          f"pressure {r['beta_pressure']:+9.1f} (z={r['z_pressure']:+6.2f}) "
          f"[pressure EXPECTED to survive: a stadium is not a pressure vessel]")
    for y in ("launch_speed", "launch_angle"):
        rr = fit(prim, y=y, label=f"{y} placebo")
        R[f"h2_placebo_{y}"] = rr
        print(f"  {y:14s} placebo  pressure z={rr['z_pressure']:+6.2f}  "
              f"vapour z={rr['z_vapor']:+6.2f}  [set at contact; density cannot touch them]")

    R["h2_tempbins"] = fit(prim, temp_ctrl="bins",
                           label="nonparametric 1C temperature bins")
    rb = R["h2_tempbins"]
    print(f"  nonparam temp bins   pressure {rb['beta_pressure']:+9.1f} (z={rb['z_pressure']:+6.2f})"
          f"   vapour {rb['beta_vapor']:+9.1f} (z={rb['z_vapor']:+6.2f})"
          f"   equal&opp z={rb['z_equal_and_opposite']:+6.2f}")

    perms = [fit(prim, rng=np.random.default_rng(SEED + 900 + i))["beta_vapor"]
             for i in range(min(args.perm, 60))]
    R["h2_permutation"] = {"n": len(perms), "mean": float(np.mean(perms)),
                           "sd": float(np.std(perms)),
                           "observed": R["h2_1_primary"]["beta_vapor"]}
    print(f"  permutation null (n={len(perms)}): vapour mean={np.mean(perms):+.1f} "
          f"sd={np.std(perms):.1f}  vs observed {R['h2_1_primary']['beta_vapor']:+.1f}")

    R["h2_planted"] = []
    for dose in (PHYSICS_FT_PER_KGM3, 5 * PHYSICS_FT_PER_KGM3):
        pr = fit(prim, planted=dose, label=f"planted {dose:.0f}")
        net = pr["beta_vapor"] - R["h2_1_primary"]["beta_vapor"]
        R["h2_planted"].append({"dose": dose, "recovered_net": net,
                                "ratio": net / dose, "se": pr["se_vapor"]})
        print(f"  planted vapour slope {dose:+8.0f} -> recovered net {net:+8.1f} "
              f"(ratio {net/dose:.3f})")

    print("\n== H2-4 Coors calibration (reported, not fitted) ==")
    co = d[d.is_coors]
    if len(co):
        drho = float(prim.rho.mean() - co.rho.mean())
        implied = drho * abs(R["h2_1_primary"]["beta_vapor"])
        R["h2_4_coors"] = {"n": int(len(co)), "coors_mean_dist": float(co.hit_distance_sc.mean()),
                           "other_mean_dist": float(prim.hit_distance_sc.mean()),
                           "delta_rho": drho, "implied_extra_ft_from_fit": implied}
        print(f"  Coors rho {co.rho.mean():.4f} vs {prim.rho.mean():.4f} "
              f"(delta {drho:+.4f} kg/m3)")
        print(f"  fitted vapour slope implies Coors carries {implied:+.1f} ft farther "
              f"(folklore/physics ~ +25 to +40 ft)")

    print("\n== H2-3 corn x Jul10-Aug31 on CARRY (label permutation, never game-clustered) ==")
    cw = ((prim.is_corn) & (prim.doy.between(WIN_LO, WIN_HI))).astype(float).values
    obs = fit(prim, extra_cell=cw, label="corn x window DiD")
    parks = sorted(prim.park_id.unique().tolist())
    corn_parks = sorted(prim[prim.is_corn].park_id.unique().tolist())
    rng = np.random.default_rng(SEED)
    null = []
    for i in range(60):
        fake = set(rng.choice(parks, len(corn_parks), replace=False).tolist())
        c = (prim.park_id.isin(fake) & prim.doy.between(WIN_LO, WIN_HI)).astype(float).values
        null.append(fit(prim, extra_cell=c)["beta_corn_window"])
    null = np.array(null)
    p = float(np.mean(np.abs(null - null.mean()) >= abs(obs["beta_corn_window"] - null.mean())))
    R["h2_3_corn_did"] = {"beta_ft": obs["beta_corn_window"],
                          "se_game_clustered_OVERSTATED": obs["se_corn_window"],
                          "label_null_mean": float(null.mean()), "label_null_sd": float(null.std()),
                          "honest_z": float((obs["beta_corn_window"] - null.mean()) / null.std()),
                          "perm_p": p, "n_perm": len(null), "n_corn_parks": len(corn_parks)}
    print(f"  corn x window carry effect {obs['beta_corn_window']:+.3f} ft "
          f"(game-clustered se {obs['se_corn_window']:.3f} -> OVERSTATED)")
    print(f"  corn-label null: mean={null.mean():+.3f} sd={null.std():.3f} -> "
          f"honest z={(obs['beta_corn_window']-null.mean())/null.std():+.2f}  perm p={p:.3f}")

    json.dump(R, open(os.path.join(OUT, "carry_results.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'carry_results.json')}")


if __name__ == "__main__":
    main()
