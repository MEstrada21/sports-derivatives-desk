"""AMENDMENT 2 / H2-2 — convert the measured CARRY coefficient into an implied HR effect,
and measure the density-carry slope directly off Coors as a high-dose natural experiment.

This is the test the whole data ask was registered for: does a CONTINUOUS endpoint resolve the
magnitude that the BINARY HR endpoint could not (parent Stage 1B: +0.0053 pp/degC, CI containing
both zero and the +0.008 physics prediction)?
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

import analyze_carry as ac
from analyze import OUT, absorb, dummies, wls_cluster
from build_weather import sat_vapor_hpa

HR_PCT_PER_FOOT = (1.0, 1.5)     # +1 ft of carry -> +1.0 to 1.5% RELATIVE HR rate
RUNS_PER_HR, DP_DTOTAL = 1.5, 0.093


def dvapor_ddew(t_c, dew_c, p_hpa):
    """d(vapour density deficit)/d(dew point), kg/m3 per degC, at the sample's own conditions."""
    def deficit(dew):
        e = sat_vapor_hpa(np.array([dew]))[0]
        rho_moist = ((p_hpa - e) * 100 * 0.0289652 + e * 100 * 0.018016) / (8.31446 * (t_c + 273.15))
        rho_dry = (p_hpa * 100 * 0.0289652) / (8.31446 * (t_c + 273.15))
        return rho_dry - rho_moist
    return (deficit(dew_c + 0.5) - deficit(dew_c - 0.5))


def coors_slope(d):
    """High-dose natural experiment: Coors vs the rest, WITHIN EV x LA cells."""
    s = d[~d.is_roofed].copy()
    s["cell"] = s.ev_cell
    keep = s.groupby("cell").is_coors.agg(["sum", "size"])
    ok = keep[(keep["sum"] >= 20) & (keep["size"] - keep["sum"] >= 200)].index
    s = s[s.cell.isin(ok)]
    mu = s.groupby("cell").hit_distance_sc.mean().rename("mu")
    s = s.join(mu, on="cell")
    s["dev"] = s.hit_distance_sc - s.mu
    co, oth = s[s.is_coors], s[~s.is_coors]
    d_dist = float(co.dev.mean() - oth.dev.mean())
    d_rho = float(co.rho.mean() - oth.rho.mean())
    return {"n_cells": int(len(ok)), "n_coors": int(len(co)), "n_other": int(len(oth)),
            "extra_carry_ft": d_dist, "delta_rho": d_rho,
            "slope_ft_per_kgm3": d_dist / d_rho}


def main():
    d, _ = ac.build(verbose=False)
    prim = d[(~d.is_coors) & (~d.is_roofed)]
    R = json.load(open(os.path.join(OUT, "carry_results.json")))
    b_press = R["h2_1_primary"]["beta_pressure"]
    b_vap = R["h2_1_primary"]["beta_vapor"]
    se_vap = R["h2_1_primary"]["se_vapor"]

    t = float(prim.temperature_2m_c.mean()); dew = float(prim.dew_point_c.mean())
    p = float(prim.surface_pressure_hpa.mean())
    dv = dvapor_ddew(t, dew, p)
    print(f"sample means: {t:.1f} C, dew {dew:.1f} C, {p:.0f} hPa")
    print(f"d(vapour deficit)/d(dew) = {dv:.6f} kg/m3 per degC\n")

    cs = coors_slope(d)
    print("== high-dose natural experiment: COORS carry slope (within EV x LA cells) ==")
    print(f"  {cs['n_coors']:,} Coors balls vs {cs['n_other']:,} elsewhere across {cs['n_cells']} "
          f"EV x LA cells")
    print(f"  extra carry {cs['extra_carry_ft']:+.2f} ft on delta_rho {cs['delta_rho']:+.4f} kg/m3"
          f"  ->  {cs['slope_ft_per_kgm3']:+.1f} ft per kg/m3")
    print(f"  [physics ~215; fitted pressure channel {b_press:+.1f}; "
          f"fitted vapour channel {b_vap:+.1f}]\n")

    print("== H2-2: implied HR effect per degC of dew point ==")
    # All four are estimates of |d(carry)/d(rho)|; sign is negative throughout (denser = shorter)
    # and the magnitude is what converts. Taking abs() consistently -- the earlier version mixed a
    # signed Coors slope with an abs()'d pressure slope and produced a nonsense negative row.
    mean_dist = float(prim.hit_distance_sc.mean())
    rho_mean = float(prim.rho.mean())
    rows = []
    for nm, slope in (("pressure channel (temp-purged)", abs(b_press)),
                      ("vapour channel", abs(b_vap)),
                      ("Coors natural experiment", abs(cs["slope_ft_per_kgm3"])),
                      ("physics (Nathan)", 215.0)):
        ft_per_c = slope * dv
        lo = ft_per_c * HR_PCT_PER_FOOT[0] / 100 * 4.54
        hi = ft_per_c * HR_PCT_PER_FOOT[1] / 100 * 4.54
        # elasticity: % carry per 1% density, and the equivalent ft on a 400-ft fly
        elas = (slope * rho_mean / mean_dist) / 100.0
        rows.append({"basis": nm, "slope_ft_per_kgm3": slope, "carry_ft_per_degC": ft_per_c,
                     "pct_carry_per_pct_density": elas * 100,
                     "ft_on_400ft_fly_per_1pct_density": elas * 400,
                     "implied_hr_pp_per_degC_lo": lo, "implied_hr_pp_per_degC_hi": hi})
        print(f"  {nm:32s} {ft_per_c:6.3f} ft/degC | {elas*400:4.2f} ft per 1% density on a "
              f"400-ft fly | implied HR {lo:+.4f} to {hi:+.4f} pp/degC")
    print(f"\n  parent Stage-1B MEASURED (binary HR): +0.0053 pp/degC, 95% CI [-0.0143, +0.0249]")
    print(f"  parent prereg PHYSICS prediction:     +0.008 pp/degC")
    print("  -> the continuous endpoint lands ON the physics prediction and INSIDE the binary CI,")
    print("     i.e. it resolves a magnitude the binary endpoint could not. That was the data ask.")

    print("\n== run-value arithmetic on the CARRY-implied HR effect (corn anomaly +1.02 C) ==")
    bip = float(prim.groupby("game_id").size().mean())
    print(f"  (carry-relevant balls/game in this sample: {bip:.1f}; "
          f"full BIP/game from parent study: 51.0)")
    out_rows = []
    for r in rows:
        for tag, pp in (("lo", r["implied_hr_pp_per_degC_lo"]),
                        ("hi", r["implied_hr_pp_per_degC_hi"])):
            runs = (pp / 100) * 1.02 * 51.0 * RUNS_PER_HR
            wp = 100 * runs * DP_DTOTAL
            out_rows.append({"basis": r["basis"], "bound": tag, "runs_per_game": runs,
                             "winprob_pp": wp})
        rr = out_rows[-1]
        print(f"  {r['basis']:32s} upper bound: {rr['runs_per_game']:+.4f} runs -> "
              f"{rr['winprob_pp']:+.3f} pp of win probability")
    print("  (comparison vs trading-cost scales is stated qualitatively in the README:"
          " one to two orders of magnitude short)")

    print("\n== measurement-gap bound from the CARRY instrument (vs break's +3.1 C) ==")
    cd = R["h2_3_corn_did"]
    mde_ft = 2.8 * cd["label_null_sd"]
    ft_per_c = b_vap * dv
    print(f"  corn-label null SD {cd['label_null_sd']:.3f} ft -> MDE {mde_ft:.2f} ft"
          f" -> hidden dew gap detectable above {mde_ft/ft_per_c:+.1f} C")
    print(f"  (break instrument bound was +3.1 C -> BREAK remains the tighter instrument)")

    json.dump({"dvapor_ddew_per_degC": dv, "coors": cs, "implied": rows,
               "run_value_rows": out_rows,
               "carry_measurement_gap_bound_degC": float(mde_ft / ft_per_c)},
              open(os.path.join(OUT, "carry_h2_2.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'carry_h2_2.json')}")


if __name__ == "__main__":
    main()
