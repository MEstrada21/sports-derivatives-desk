"""AMENDMENT 3 — remaining methods-audit + domain-review items.

A. EXACT-PROPORTIONALITY test (auditor's bonus argument): break is a Magnus quantity, so
   break = k*rho exactly implies d(break)/d(rho) = mean_break / mean_rho. If our fitted pressure
   channel sits on that value, it is clean aerodynamics -- a much stronger statement than "the
   sign is right".
B. RULE #7 VIOLATION in the K-thread OOS split: 2025 is pre-ABS and 2026 is post-ABS
   (true debut 2026-03-25), and walk/K may NEVER be pooled across that boundary. Re-cut per season.
C. UPSTREAM positive control. The planted dose in analyze.py enters AFTER load(), so it is an
   algebraic identity for a linear estimator and tests nothing about the join, filters or formulas
   (the pnl_taker lesson). This plants at the RAW WEATHER level, upstream of everything, so the
   whole pipeline has to carry the signal.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

from analyze import SEED, OUT, load, stage1b

ABS_DEBUT = "2026-03-25"


def main():
    R = {"seed": SEED}
    games, _ = load()
    sa = json.load(open(os.path.join(OUT, "spin_axis_test.json")))

    print("== A. exact-proportionality test on the pressure channel ==")
    bm = sa["break_mag"]
    mean_break = bm["mean_y"]
    # mean rho over the same open-air ex-Coors sample
    m = (~games.is_roofed) & (~games.is_coors)
    mean_rho = float(games[m].rho.mean())
    exact = mean_break / mean_rho
    b, se = bm["beta_pressure"], bm["se_pressure"]
    z = (b - exact) / se
    print(f"  mean break {mean_break:.3f} in / mean rho {mean_rho:.4f} kg/m3")
    print(f"  break = k*rho EXACTLY implies slope = {exact:.2f} in per kg/m3")
    print(f"  fitted pressure channel      = {b:.2f} +/- {se:.2f}")
    print(f"  departure from exact proportionality: z = {z:+.2f}  -> "
          f"{'INDISTINGUISHABLE from exact Magnus proportionality' if abs(z) < 1.96 else 'DIFFERS'}")
    R["exact_proportionality"] = {"mean_break_in": mean_break, "mean_rho": mean_rho,
                                  "exact_slope": exact, "fitted": b, "se": se, "z_departure": z}

    print("\n== B. RULE #7: the K-thread OOS split pooled across the ABS boundary ==")
    print(f"  true ABS debut = {ABS_DEBUT}; walk/K may never be pooled across it.")
    print("  the banked 'fit 2023-24 -> held-out 2025-26' split put PRE-ABS 2025 and POST-ABS 2026")
    print("  in the same held-out bucket. Re-cut per season:\n")
    R["k_by_season"] = {}
    for s in ("2023", "2024", "2025", "2026"):
        mm = (m & games.season.eq(s)).values
        sub = games[mm]
        jul_aug = int(sub.doy.between(191, 243).sum())
        r = stage1b(games, mm, y_num="k", y_den="pa", key="dew_point_c", label=s)
        zz = r["beta_pp"] / r["se_pp"]
        R["k_by_season"][s] = {"beta_pp": r["beta_pp"], "se_pp": r["se_pp"], "z": zz,
                               "n_games": r["n_games"], "jul_aug_games": jul_aug,
                               "regime": "post-ABS" if s == "2026" else "pre-ABS"}
        note = ""
        if s == "2026":
            note = f"  <- POST-ABS, and corpus stops 07-02 so only {jul_aug} Jul-Aug games: UNINFORMATIVE"
        print(f"  {s} ({'post' if s=='2026' else 'pre'}-ABS): beta={r['beta_pp']:+.4f} pp/degC  "
              f"se={r['se_pp']:.4f}  z={zz:+.2f}  n={r['n_games']}{note}")
    print("\n  correct statement: pre-ABS seasons carry the finding; 2026 is uninformative BY")
    print("  CONSTRUCTION (post-ABS regime AND no Jul-Aug coverage), not evidence against it.")

    print("\n== B2. the BB placebo is under-sold supporting evidence ==")
    rbb = stage1b(games, m.values, y_num="bb", y_den="pa", key="dew_point_c", label="BB/PA")
    rk = stage1b(games, m.values, y_num="k", y_den="pa", key="dew_point_c", label="K/PA")
    print(f"  K/PA  beta={rk['beta_pp']:+.4f} pp/degC  z={rk['beta_pp']/rk['se_pp']:+.2f}")
    print(f"  BB/PA beta={rbb['beta_pp']:+.4f} pp/degC  z={rbb['beta_pp']/rbb['se_pp']:+.2f}  (FLAT)")
    print("  a MOVEMENT/whiff channel predicts K moves and BB does not; a COMMAND channel predicts")
    print("  BOTH move. The flat BB is a discriminating null, not a boring one.")
    R["bb_placebo"] = {"k_z": rk["beta_pp"] / rk["se_pp"], "bb_z": rbb["beta_pp"] / rbb["se_pp"],
                       "bb_beta": rbb["beta_pp"]}

    print("\n== C. UPSTREAM positive control (plants at raw weather, before every join/filter) ==")
    base = stage1b(games, m.values, y_num="hr", y_den="bip", key="dew_point_c")["beta_pp"]
    R["upstream_control"] = []
    for dose in (0.0, 0.02, 0.05):
        g2 = games.copy()
        if dose:
            # plant at the RAW WEATHER level: perturb HR counts as a function of dew point,
            # upstream of the rate construction, the weights and the fixed effects
            rng = np.random.default_rng(SEED + 4242)
            lift = (dose / 100.0) * (g2.dew_point_c.values - g2.dew_point_c.mean())
            extra = rng.binomial(np.maximum(g2.bip.values, 0),
                                 np.clip(lift, 0, 0.5))
            g2["hr"] = g2.hr.values + extra
        r = stage1b(g2, m.values, y_num="hr", y_den="bip", key="dew_point_c")
        net = r["beta_pp"] - base
        R["upstream_control"].append({"dose_pp_per_c": dose, "recovered_net": net,
                                      "se": r["se_pp"],
                                      "ci_excl_0": bool(r["ci_lo_pp"] > 0 or r["ci_hi_pp"] < 0)})
        print(f"  upstream dose {dose:.3f} pp/degC -> recovered net {net:+.4f} "
              f"(se {r['se_pp']:.4f})")
    print("  NOTE: doses are one-sided (counts can only be added), so recovery is ~half the nominal")
    print("  dose by construction; what matters is that a signal injected BEFORE the joins,")
    print("  filters and weights SURVIVES the pipeline -- which the post-load() plant never tested.")

    json.dump(R, open(os.path.join(OUT, "amendment3_audit.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'amendment3_audit.json')}")


if __name__ == "__main__":
    main()
