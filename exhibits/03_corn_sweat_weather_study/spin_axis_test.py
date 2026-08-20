"""AMENDMENT 3 — THE SPIN-AXIS TEST (both reviewers named this the decisive experiment).

Question: the humidity channel is NON-aerodynamic (pressure->spin is z~0 while vapour->spin is
z~-10). What IS it? Three candidates, and they make DIFFERENT predictions about RELEASE kinematics:

  GRIP / ball-hand friction   -> the pitcher cannot impart the intended spin: rate falls, the AXIS
                                 shifts, and axis CONSISTENCY (resultant length R) degrades.
  BALL SURFACE / seam-wake    -> release kinematics UNCHANGED; only the aerodynamic response per
                                 unit spin changes (break-per-1000-rpm moves, axis and R do not).
  OPTICAL MEASUREMENT quality -> an artifact of tracking in humid air; would tend to hit the
                                 hardest-to-track pitches and need not respect either pattern.

Discriminator implemented here, all under the tightened spec (first-pitch-hour FE + park x season
FE, per the methods audit):
  1. axis components mean(sin), mean(cos)  -- does the axis MOVE?
  2. R = release-axis consistency          -- does release get SCATTERED?
  3. eff = break per 1000 rpm              -- does aerodynamic response per unit spin change?
  4. pitch-type heterogeneity of the excess ratio -- grip predicts breaking balls hurt MOST
     (they need the most finger friction); the methods audit reports the OPPOSITE ordering.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

from analyze import SEED, OUT, load, absorb, dummies, wls_cluster, linear_combo

FASTBALLS = {"FF", "SI", "FC", "FA"}
BREAKING = {"SL", "CU", "KC", "ST", "SV", "CS"}
OFFSPEED = {"CH", "FS", "FO", "SC"}


def tightened(d, y, extra=None):
    """Tightened spec: pitcher x pitch_type x season FE absorbed; park x season + hour FE."""
    d = d.copy()
    d["fe"] = d.pitcher_id + "|" + d.pitch_type.astype(str) + "|" + d.season
    d["park_season"] = d.park_id + "|" + d.season
    reg = {"rho_dry": d.rho_dry.values, "vapor_deficit": d.vapor_density_deficit.values,
           "temp": d.temperature_2m_c.values, "temp2": d.temperature_2m_c.values ** 2,
           "wind": d.wind_speed_10m_ms.values, "precip": d.precipitation_mm.values}
    if extra is not None:
        reg.update(extra)
    X = pd.concat([pd.DataFrame(reg),
                   dummies(d.park_season).reset_index(drop=True),
                   dummies(d.fp_hour.astype(str)).reset_index(drop=True),
                   dummies(d.season_month).reset_index(drop=True)], axis=1)
    X = X.loc[:, X.std(numeric_only=True) > 0]
    cols = list(X.columns)
    frame = pd.concat([pd.DataFrame({y: d[y].values, "fe": d.fe.values, "n": d.n.values}), X],
                      axis=1)
    dm = absorb(frame, [y] + cols, "fe", "n")
    res, beta, V = wls_cluster(dm[y].values, dm[cols].values, d.n.values, d.game_id.values, cols)
    s, se, z = linear_combo(beta, V, cols, {"rho_dry": 1.0, "vapor_deficit": 1.0})
    mean_y = float(np.average(d[y], weights=d.n))
    return {"y": y, "n_pitches": int(d.n.sum()), "mean_y": mean_y,
            "beta_pressure": res["rho_dry"][0], "se_pressure": res["rho_dry"][1],
            "z_pressure": res["rho_dry"][0] / res["rho_dry"][1],
            "beta_vapor": res["vapor_deficit"][0], "se_vapor": res["vapor_deficit"][1],
            "z_vapor": res["vapor_deficit"][0] / res["vapor_deficit"][1],
            "z_equal_and_opposite": z,
            "excess_ratio": (abs(res["vapor_deficit"][0]) / abs(res["rho_dry"][0])
                             if res["rho_dry"][0] else np.nan),
            # natural units: % change per p5-p95 swing of each channel
            "pct_per_p5p95_vapor": 100 * res["vapor_deficit"][0] * 0.00581 / mean_y
            if mean_y else np.nan}


def main():
    games, _ = load()
    ax = pd.read_parquet(os.path.join(OUT, "axis_cells.parquet"))
    ax["game_id"] = ax.game_id.astype(str)
    g = games[["game_id", "park_id", "season", "season_month", "rho_dry", "vapor_density_deficit",
               "temperature_2m_c", "wind_speed_10m_ms", "precipitation_mm", "is_roofed",
               "is_coors", "first_pitch_utc"]].copy()
    g["fp_hour"] = pd.to_datetime(g.first_pitch_utc, utc=True, format="ISO8601").dt.hour
    d = ax.merge(g, on="game_id", how="inner")
    d = d[(d.n >= 3) & (~d.is_coors) & (~d.is_roofed)].copy()
    print(f"sample: {len(d):,} cells / {int(d.n.sum()):,} pitches / {d.game_id.nunique():,} games\n")
    R = {"seed": SEED, "n_pitches": int(d.n.sum())}

    print("== THE DISCRIMINATOR: release kinematics vs aerodynamic response ==")
    print("   GRIP predicts axis MOVES + consistency R FALLS + rate falls")
    print("   SURFACE predicts release UNCHANGED, only break-per-rpm moves\n")
    labels = {"spin": "release spin rate (rpm)", "ax_sin": "axis sin component",
              "ax_cos": "axis cos component", "R": "axis CONSISTENCY (resultant)",
              "eff": "break per 1000 rpm (aero response)", "break_mag": "break magnitude (in)",
              "velo": "release velocity (mph)"}
    for y in ("spin", "ax_sin", "ax_cos", "R", "eff", "break_mag", "velo"):
        r = tightened(d, y)
        R[y] = r
        print(f"  {labels[y]:34s} vapour z={r['z_vapor']:+7.2f}  pressure z={r['z_pressure']:+6.2f}"
              f"   vapour effect over p5-p95 humidity = {r['pct_per_p5p95_vapor']:+6.2f}%")

    print("\n== pitch-type heterogeneity of the vapour EXCESS (grip predicts breaking balls WORST) ==")
    def fam(pt):
        return ("fastball" if pt in FASTBALLS else "breaking" if pt in BREAKING
                else "offspeed" if pt in OFFSPEED else "other")
    d["family"] = d.pitch_type.astype(str).map(fam)
    R["by_family"] = {}
    for f in ("fastball", "breaking", "offspeed"):
        sub = d[d.family == f]
        if len(sub) < 5000:
            continue
        rb = tightened(sub, "break_mag")
        rs = tightened(sub, "spin")
        R["by_family"][f] = {"break": rb, "spin": rs}
        print(f"  {f:9s} n={int(sub.n.sum()):>9,}  break excess ratio {rb['excess_ratio']:5.2f}"
              f"  (vapour z={rb['z_vapor']:+6.2f})   spin vapour z={rs['z_vapor']:+6.2f}")
    fams = R["by_family"]
    if "fastball" in fams and "breaking" in fams:
        fb, bb = fams["fastball"]["break"]["excess_ratio"], fams["breaking"]["break"]["excess_ratio"]
        print(f"\n  ordering: fastball {fb:.2f} vs breaking {bb:.2f}  -> "
              f"{'AGAINST grip (breaking balls need the MOST finger friction, yet show the LEAST excess)' if fb > bb else 'consistent with grip'}")
        R["family_ordering_against_grip"] = bool(fb > bb)

    json.dump(R, open(os.path.join(OUT, "spin_axis_test.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'spin_axis_test.json')}")


if __name__ == "__main__":
    main()
