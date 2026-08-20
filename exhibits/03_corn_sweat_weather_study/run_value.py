"""Convert the measured coefficients into runs and into win probability. This is arithmetic on
OUR OWN coefficients -- it is NOT a market read. Stage 3 (does the closing total misprice humid
games?) was NOT run: it is gated on Stage 1B clearing, and Stage 1B did not clear.

The comparison against trading-cost scales is stated qualitatively in the exhibit README (the
corn-anomaly effect lands one to two orders of magnitude below exchange fee levels); the fee
constants themselves are out of scope for this public exhibit.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

from analyze import OUT, load

# linear-weights conversions
WOBA_ON_CONTACT = 0.370     # league wOBA on balls in play incl. HR
WOBA_SCALE = 1.15           # runs per wOBA point per PA
RUNS_PER_HR = 1.5
DP_DTOTAL = 0.093           # d(P win)/d(runs) near a typical total


def main():
    games, _ = load()
    m = (~games.is_roofed) & (~games.is_coors)
    g = games[m]
    bip_g, pa_g = float(g.bip.mean()), float(g.pa.mean())

    res = json.load(open(os.path.join(OUT, "results.json")))
    diag = json.load(open(os.path.join(OUT, "diagnostics.json")))
    b_hr = res["s1b_primary"]["beta_pp"]
    b_hr_hi = res["s1b_primary"]["ci_hi_pp"]
    b_k = res["s1b_k_placebo"]["beta_pp"]
    corn = json.load(open(os.path.join(OUT, "results.json")))["stage2_ex_sutter"]["diff_c"]
    swing_p5p95 = diag["units"]["dew_resid_p5_p95_c"]

    print(f"BIP/game={bip_g:.1f}  PA/game={pa_g:.1f}  "
          f"corn anomaly={corn:+.2f} C  p5-p95 dew swing={swing_p5p95:.2f} C\n")

    rows = []
    for sname, sw in (("CORN anomaly (the actual hypothesis)", corn),
                      ("p5-p95 dew swing (extreme, not corn)", swing_p5p95)):
        hr_runs = (b_hr / 100) * sw * bip_g * RUNS_PER_HR
        hr_runs_hi = (b_hr_hi / 100) * sw * bip_g * RUNS_PER_HR
        k_runs = -(b_k / 100) * sw * pa_g * (WOBA_ON_CONTACT / WOBA_SCALE)
        tot = hr_runs + k_runs
        rows.append({
            "scenario": sname, "swing_C": sw,
            "HR_channel_runs": hr_runs, "HR_channel_runs_upperCI": hr_runs_hi,
            "K_channel_runs": k_runs, "total_runs": tot,
            "winprob_pp": 100 * tot * DP_DTOTAL,
            "winprob_pp_HRonly": 100 * hr_runs * DP_DTOTAL})

    df = pd.DataFrame(rows)
    for r in rows:
        print(f"{r['scenario']}  (swing {r['swing_C']:.2f} C)")
        print(f"   HR channel (carry):        {r['HR_channel_runs']:+.4f} runs/game "
              f"(95% upper {r['HR_channel_runs_upperCI']:+.4f})")
        print(f"   K channel (grip/spin):     {r['K_channel_runs']:+.4f} runs/game   "
              f"[EXPLORATORY, survives family-wise perm]")
        print(f"   TOTAL:                     {r['total_runs']:+.4f} runs/game "
              f"-> {r['winprob_pp']:+.3f} pp of win probability\n")

    df.to_csv(os.path.join(OUT, "run_value.csv"), index=False)
    json.dump({"bip_per_game": bip_g, "pa_per_game": pa_g, "corn_anomaly_c": corn,
               "p5_p95_dew_swing_c": swing_p5p95, "rows": rows,
               "note": "arithmetic on our own coefficients; NO market data was read (stage 3 gated"
                       " and unearned)"},
              open(os.path.join(OUT, "run_value.json"), "w"), indent=2, default=str)
    print(f"WROTE {os.path.join(OUT, 'run_value.json')}")


if __name__ == "__main__":
    main()
