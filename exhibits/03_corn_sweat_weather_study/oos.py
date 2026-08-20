"""Held-out check on the ONE exploratory survivor (dew point -> strikeout rate).

Fit-era 2023-2024, held-out era 2025-2026. The coefficient was discovered in the pooled sample,
so the pooled number is in-sample for it; the held-out era is the honest test. Also re-runs the
HR primary per era for context.
"""
from __future__ import annotations
import json, os
import numpy as np

from analyze import OUT, load, stage1b

ERAS = {"fit_2023_2024": ("2023", "2024"), "heldout_2025_2026": ("2025", "2026")}


def main():
    games, _ = load()
    base = (~games.is_roofed) & (~games.is_coors)
    R = {}
    print(f"{'era':20s} {'endpoint':10s} {'beta pp/C':>11s} {'se':>9s} {'z':>7s}  95% CI")
    for era, yrs in ERAS.items():
        m = (base & games.season.isin(yrs)).values
        for nm, yn, yd in (("K/PA", "k", "pa"), ("HR/BIP", "hr", "bip")):
            r = stage1b(games, m, y_num=yn, y_den=yd, key="dew_point_c", label=f"{era}|{nm}")
            R[f"{era}|{nm}"] = r
            z = r["beta_pp"] / r["se_pp"]
            print(f"{era:20s} {nm:10s} {r['beta_pp']:+11.5f} {r['se_pp']:9.5f} {z:+7.2f}  "
                  f"[{r['ci_lo_pp']:+.5f}, {r['ci_hi_pp']:+.5f}]  n={r['n_games']}")

    kf, kh = R["fit_2023_2024|K/PA"], R["heldout_2025_2026|K/PA"]
    same_sign = np.sign(kf["beta_pp"]) == np.sign(kh["beta_pp"])
    holds = same_sign and (kh["ci_hi_pp"] < 0 if kh["beta_pp"] < 0 else kh["ci_lo_pp"] > 0)
    R["verdict_K"] = {"same_sign": bool(same_sign),
                      "heldout_ci_excludes_zero": bool(kh["ci_lo_pp"] > 0 or kh["ci_hi_pp"] < 0),
                      "replicates_out_of_sample": bool(holds),
                      "fit_beta": kf["beta_pp"], "heldout_beta": kh["beta_pp"]}
    print(f"\nK/PA out-of-sample: fit {kf['beta_pp']:+.5f} -> held-out {kh['beta_pp']:+.5f}  "
          f"same sign={same_sign}  held-out CI excludes 0="
          f"{kh['ci_lo_pp'] > 0 or kh['ci_hi_pp'] < 0}  => "
          f"{'REPLICATES' if holds else 'DOES NOT REPLICATE'}")

    json.dump(R, open(os.path.join(OUT, "oos.json"), "w"), indent=2, default=str)
    print(f"WROTE {os.path.join(OUT, 'oos.json')}")


if __name__ == "__main__":
    main()
