"""Follow-ups the spec-v2 run forced:

  D1  spin placebo, run properly (it NaN'd in analyze.py) -- the discriminator between an
      AIR-DENSITY channel (spin at release is unaffected; only flight is) and a GRIP channel
      (humid ball/hand -> less spin imparted -> less break).
  D2  break controlling for release spin -- if the excess vapour coefficient collapses toward the
      pressure coefficient once spin is held fixed, the excess was grip, not aerodynamics.
  D3  roofed placebo split: FIXED DOME vs RETRACTABLE. Note the prereg's roof placebo is
      mis-specified for the PRESSURE channel -- a stadium is not a pressure vessel, so barometric
      pressure inside a closed dome equals the outside value and the pressure channel is EXPECTED
      to survive. The placebo is only valid for the vapour/temperature channels.
  D4  everything restated in units that occur in nature (per realistic humidity swing), because
      "per kg/m3" is a ~100x extrapolation for the vapour channel.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

from analyze import (SEED, OUT, load, stage1a, stage1b, absorb, dummies, wls_cluster,
                     linear_combo, GAME_COLS, COORS_SLOPE_IN_PER_KGM3)


def stage1a_spin_controlled(cells, games, mask, y_col="break_mag", label="", with_spin=True):
    g = games[mask]
    d = cells.merge(g[GAME_COLS], on="game_id", how="inner")
    d = d[(d.n >= 3)].dropna(subset=["break_mag", "velo", "spin"]).copy()
    d["fe"] = d.pitcher_id + "|" + d.pitch_type.astype(str) + "|" + d.season
    base = {"rho_dry": d.rho_dry.values, "vapor_deficit": d.vapor_density_deficit.values,
            "temp": d.temperature_2m_c.values, "temp2": d.temperature_2m_c.values ** 2,
            "wind": d.wind_speed_10m_ms.values, "precip": d.precipitation_mm.values}
    if with_spin:
        base["spin"] = d.spin.values
        base["velo"] = d.velo.values
    X = pd.concat([pd.DataFrame(base), dummies(d.park_id).reset_index(drop=True),
                   dummies(d.season_month).reset_index(drop=True)], axis=1)
    cols = list(X.columns)
    frame = pd.concat([pd.DataFrame({y_col: d[y_col].values, "fe": d.fe.values, "n": d.n.values}),
                       X], axis=1)
    dm = absorb(frame, [y_col] + cols, "fe", "n")
    res, beta, V = wls_cluster(dm[y_col].values, dm[cols].values, d.n.values, d.game_id.values, cols)
    s, se, z = linear_combo(beta, V, cols, {"rho_dry": 1.0, "vapor_deficit": 1.0})
    return {"label": label, "y": y_col, "spin_controlled": with_spin, "n_pitches": int(d.n.sum()),
            "beta_pressure": res["rho_dry"][0], "se_pressure": res["rho_dry"][1],
            "beta_vapor": res["vapor_deficit"][0], "se_vapor": res["vapor_deficit"][1],
            "z_pressure": res["rho_dry"][0] / res["rho_dry"][1],
            "z_vapor": res["vapor_deficit"][0] / res["vapor_deficit"][1],
            "z_equal_and_opposite": z,
            "excess_vapor_over_pressure": res["vapor_deficit"][0] + res["rho_dry"][0]}


def residual_sd(games, mask, col):
    """SD of a game-level weather channel after park FE + season-month FE + temp + temp^2."""
    g = games[mask]
    X = pd.concat([pd.DataFrame({"c": 1.0, "t": g.temperature_2m_c.values,
                                 "t2": g.temperature_2m_c.values ** 2}),
                   dummies(g.park_id).reset_index(drop=True),
                   dummies(g.season_month).reset_index(drop=True)], axis=1).values.astype(float)
    y = g[col].values
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    return float(np.std(r)), float(np.percentile(r, 95) - np.percentile(r, 5))


def main():
    games, cells = load()
    open_mask = (~games.is_roofed) & (~games.is_coors)
    dome_mask = games.roof.eq("Dome").values
    retract_mask = games.roof.eq("Retractable").values
    D = {"seed": SEED}

    print("== D1: release-spin placebo (density cannot touch spin at release; grip can) ==")
    D["spin_placebo"] = stage1a_spin_controlled(cells, games, open_mask, y_col="spin",
                                                label="release spin", with_spin=False)
    D["velo_placebo"] = stage1a_spin_controlled(cells, games, open_mask, y_col="velo",
                                                label="release velocity", with_spin=False)
    for k in ("spin_placebo", "velo_placebo"):
        r = D[k]
        print(f"  {r['label']:18s}  pressure {r['beta_pressure']:+10.2f} (z={r['z_pressure']:+6.2f})"
              f"   vapour {r['beta_vapor']:+10.2f} (z={r['z_vapor']:+6.2f})")

    print("\n== D2: break, with and without holding release spin+velo fixed ==")
    D["break_raw"] = stage1a_spin_controlled(cells, games, open_mask, label="break (no spin ctrl)",
                                             with_spin=False)
    D["break_spinctrl"] = stage1a_spin_controlled(cells, games, open_mask,
                                                  label="break (spin+velo held fixed)",
                                                  with_spin=True)
    for k in ("break_raw", "break_spinctrl"):
        r = D[k]
        print(f"  {r['label']:32s} pressure {r['beta_pressure']:+8.2f} (z={r['z_pressure']:+6.2f})"
              f"   vapour {r['beta_vapor']:+9.2f} (z={r['z_vapor']:+6.2f})"
              f"   excess {r['excess_vapor_over_pressure']:+8.2f}   equal&opp z={r['z_equal_and_opposite']:+6.2f}")

    print("\n== D3: roof placebo split (pressure channel is EXPECTED to survive a dome) ==")
    for nm, m in (("FIXED DOME (Tropicana)", dome_mask), ("RETRACTABLE (often open)", retract_mask)):
        r = stage1a(cells, games, m, label=nm)
        D[f"roof_{nm.split()[0].lower()}"] = r
        print(f"  {nm:26s} n_pitch={r['n_pitches']:8d}  pressure {r['beta_pressure_channel']:+8.2f}"
              f" (z={r['z_pressure']:+6.2f})   vapour {r['beta_vapor_channel']:+9.2f}"
              f" (z={r['z_vapor']:+6.2f})")

    print("\n== D4: effects in units that occur in nature ==")
    sd_v, p90_v = residual_sd(games, open_mask, "vapor_density_deficit")
    sd_r, p90_r = residual_sd(games, open_mask, "rho_dry")
    sd_d, p90_d = residual_sd(games, open_mask, "dew_point_c")
    raw_v = float(games[open_mask].vapor_density_deficit.max() -
                  games[open_mask].vapor_density_deficit.min())
    D["units"] = {"vapor_resid_sd_kgm3": sd_v, "vapor_resid_p5_p95_kgm3": p90_v,
                  "vapor_full_observed_range_kgm3": raw_v,
                  "rho_dry_resid_sd_kgm3": sd_r, "dew_resid_sd_c": sd_d,
                  "dew_resid_p5_p95_c": p90_d}
    br = D["break_raw"]
    print(f"  vapour channel residual SD = {sd_v:.5f} kg/m3 (p5-p95 = {p90_v:.5f}; "
          f"full observed range = {raw_v:.5f})")
    print(f"  -> break effect over a p5-p95 humidity swing: "
          f"{br['beta_vapor'] * p90_v:+.4f} inches  (mean break ~15 in)")
    print(f"  -> the DENSITY-only part of that (at the pressure-channel slope): "
          f"{-br['beta_pressure'] * p90_v:+.4f} inches")
    print(f"  dew-point residual SD = {sd_d:.3f} C (p5-p95 = {p90_d:.3f} C)")

    res = json.load(open(os.path.join(OUT, "results.json")))
    b1 = res["s1b_primary"]
    print(f"  -> HR/BIP over a p5-p95 dew swing: {b1['beta_pp'] * p90_d:+.4f} pp "
          f"(CI [{b1['ci_lo_pp'] * p90_d:+.4f}, {b1['ci_hi_pp'] * p90_d:+.4f}]) "
          f"on a {b1['base_rate_pp']:.2f} pp base")

    print("\n== D5: market ceiling, computed from the MEASURED upper CI (not the point estimate) ==")
    bip_per_game = float((games[open_mask].bip / 1).mean())
    for nm, beta_pp in (("physics prediction", 0.008),
                        ("measured point estimate", b1["beta_pp"]),
                        ("measured 95% UPPER bound", b1["ci_hi_pp"])):
        for swing, sl in ((3.0, "corn anomaly +3C"), (p90_d, "p5-p95 dew swing")):
            d_hr_rate = beta_pp * swing / 100.0
            d_hr = d_hr_rate * bip_per_game
            d_runs = d_hr * 1.5
            d_p = d_runs * 0.093
            print(f"  {nm:26s} x {sl:20s}: {d_hr:+.4f} HR/g  {d_runs:+.4f} runs  "
                  f"{100*d_p:+.3f} pp of win prob")
    print("  (comparison vs trading-cost scales is stated qualitatively in the README:"
          " one to two orders of magnitude short)")
    D["market_ceiling"] = {"bip_per_game": bip_per_game, "dew_p5_p95_c": p90_d,
                           "beta_upper_ci_pp_per_c": b1["ci_hi_pp"],
                           "pp_winprob_at_upper_ci_3C": 0.093 * 1.5 * bip_per_game *
                                                        b1["ci_hi_pp"] * 3.0 / 100.0 * 100}

    json.dump(D, open(os.path.join(OUT, "diagnostics.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'diagnostics.json')}")


if __name__ == "__main__":
    main()
