"""AMENDMENT 3b — two items the team-lead asked to close out.

ITEM 1: ROOF-STATE SPLIT on ACTUAL roof state. The pre-registered roof placebo failed because
"roofed park" pools closed-roof games with games played with the roof OPEN. `roof_state.parquet`
(already on disk from the leverB_parkwind lane, StatsAPI `gameData.weather.condition`) gives the
real per-game state for all 7 retractable parks. This turns a broken placebo into a clean one.

  Predictions, stated before fitting:
    roof CLOSED -> VAPOUR channel ~ 0 (climate-controlled air severs it)
                   PRESSURE channel SURVIVES (a stadium is not a pressure vessel)
    roof OPEN   -> both behave like open-air
  A non-zero VAPOUR channel under a closed roof would be strong evidence the humidity channel is
  not acting through the air at all -- which is exactly the open question from Amendment 2/3.

ITEM 2: regenerate the four hard-coded COORS constants from committed code (the auditor could not
reproduce the 919-pair figure), and report the slope's sensitivity across defensible filters
instead of a single number.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

from analyze import SEED, OUT, load, absorb, dummies, wls_cluster, linear_combo, GAME_COLS

LANE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DATA_ROOT", LANE)
# Per-game ACTUAL roof state for the 7 retractable-roof parks, derived from the public
# MLB StatsAPI game feed (gameData.weather.condition: "Roof Closed"/"Dome" vs open-air
# conditions), with columns game_pk / game_date / roof_open / roof_class / fetch_ok.
ROOF = os.environ.get("ROOF_STATE_PARQUET",
                      os.path.join(ROOT, "data", "roof_state.parquet"))


def fit_break(cells, games, mask, label, y="break_mag"):
    g = games[mask]
    d = cells.merge(g[GAME_COLS], on="game_id", how="inner")
    d = d[d.n >= 3].copy()
    if len(d) < 2000:
        return {"label": label, "n_pitches": int(d.n.sum()) if len(d) else 0, "insufficient": True}
    d["fe"] = d.pitcher_id + "|" + d.pitch_type.astype(str) + "|" + d.season
    reg = pd.DataFrame({"rho_dry": d.rho_dry.values,
                        "vapor_deficit": d.vapor_density_deficit.values,
                        "temp": d.temperature_2m_c.values,
                        "temp2": d.temperature_2m_c.values ** 2,
                        "wind": d.wind_speed_10m_ms.values,
                        "precip": d.precipitation_mm.values})
    X = pd.concat([reg, dummies(d.park_id).reset_index(drop=True),
                   dummies(d.season_month).reset_index(drop=True)], axis=1)
    X = X.loc[:, X.std(numeric_only=True) > 0]
    cols = list(X.columns)
    frame = pd.concat([pd.DataFrame({y: d[y].values, "fe": d.fe.values, "n": d.n.values}), X],
                      axis=1)
    dm = absorb(frame, [y] + cols, "fe", "n")
    res, beta, V = wls_cluster(dm[y].values, dm[cols].values, d.n.values, d.game_id.values, cols)
    s, se, z = linear_combo(beta, V, cols, {"rho_dry": 1.0, "vapor_deficit": 1.0})
    return {"label": label, "n_pitches": int(d.n.sum()), "n_games": int(d.game_id.nunique()),
            "beta_pressure": res["rho_dry"][0], "se_pressure": res["rho_dry"][1],
            "z_pressure": res["rho_dry"][0] / res["rho_dry"][1],
            "beta_vapor": res["vapor_deficit"][0], "se_vapor": res["vapor_deficit"][1],
            "z_vapor": res["vapor_deficit"][0] / res["vapor_deficit"][1],
            "z_equal_and_opposite": z, "insufficient": False}


def coors_slope(cells, games, min_coors, min_other, min_n):
    """Regenerated from code: same pitchers, Coors vs elsewhere, within pitcher x pitch_type."""
    d = cells.merge(games[["game_id", "park_id", "rho", "is_coors", "is_roofed"]],
                    on="game_id", how="inner")
    d = d[(d.n >= min_n) & (~d.is_roofed)].copy()
    d["fe"] = d.pitcher_id + "|" + d.pitch_type.astype(str)
    agg = d.groupby("fe").is_coors.agg(["sum", "size"])
    keep = agg[(agg["sum"] >= min_coors) & (agg["size"] - agg["sum"] >= min_other)].index
    s = d[d.fe.isin(keep)]
    if not len(s):
        return None
    co, oth = s[s.is_coors], s[~s.is_coors]
    bc = np.average(co.break_mag, weights=co.n); bo = np.average(oth.break_mag, weights=oth.n)
    rc = np.average(co.rho, weights=co.n); ro = np.average(oth.rho, weights=oth.n)
    return {"n_pairs": int(len(keep)), "min_coors": min_coors, "min_other": min_other,
            "min_n": min_n, "break_coors": float(bc), "break_other": float(bo),
            "rho_coors": float(rc), "rho_other": float(ro),
            "slope_in_per_kgm3": float((bo - bc) / (ro - rc)),
            "break_ratio_pct": float(100 * bc / bo), "rho_ratio_pct": float(100 * rc / ro)}


def main():
    games, cells = load()
    R = {"seed": SEED}

    print("== ITEM 1: roof-state split on ACTUAL roof state (no new pull) ==")
    rs = pd.read_parquet(ROOF)
    rs["game_id"] = rs.game_pk.astype(str)
    rs = rs[rs.fetch_ok].drop_duplicates("game_id")
    print(f"  roof_state.parquet: {len(rs)} games, {rs.game_date.min()} -> {rs.game_date.max()}, "
          f"{int((~rs.roof_open).sum())} closed / {int(rs.roof_open.sum())} open")
    g = games.merge(rs[["game_id", "roof_open", "roof_class"]], on="game_id", how="left")
    matched = g.roof_open.notna().sum()
    print(f"  matched to our corpus: {matched} games "
          f"({int((g.roof_open == False).sum())} closed / {int((g.roof_open == True).sum())} open)\n")

    closed = (g.roof_open == False).values
    openroof = (g.roof_open == True).values
    openair = ((~g.is_roofed) & (~g.is_coors)).values

    for nm, m in (("open-air (reference)", openair),
                  ("retractable, roof OPEN", openroof),
                  ("retractable, roof CLOSED", closed)):
        r = fit_break(cells, g, m, nm)
        R[nm] = r
        if r.get("insufficient"):
            print(f"  {nm:26s} INSUFFICIENT (n={r['n_pitches']})")
            continue
        print(f"  {nm:26s} n={r['n_pitches']:>9,}  pressure {r['beta_pressure']:+8.2f} "
              f"(z={r['z_pressure']:+6.2f})   vapour {r['beta_vapor']:+9.2f} (z={r['z_vapor']:+6.2f})")

    cl, op = R["retractable, roof CLOSED"], R["retractable, roof OPEN"]
    if not cl.get("insufficient"):
        print(f"\n  PRE-STATED PREDICTIONS:")
        print(f"    vapour ~0 under a closed roof?  z={cl['z_vapor']:+.2f}  -> "
              f"{'YES, severed as predicted' if abs(cl['z_vapor'])<1.96 else 'NO, SURVIVES the roof'}")
        print(f"    pressure survives closed roof?  z={cl['z_pressure']:+.2f}  -> "
              f"{'YES (correct: not a pressure vessel)' if abs(cl['z_pressure'])>1.96 else 'no'}")
        R["roof_verdict"] = {
            "vapour_severed_by_closed_roof": bool(abs(cl["z_vapor"]) < 1.96),
            "pressure_survives_closed_roof": bool(abs(cl["z_pressure"]) > 1.96)}

    print("\n== ITEM 2: Coors constants REGENERATED from committed code ==")
    grid = []
    for mc, mo, mn in ((2, 10, 3), (2, 10, 1), (5, 20, 3), (10, 50, 3), (20, 200, 3), (1, 5, 3)):
        c = coors_slope(cells, games, mc, mo, mn)
        if c:
            grid.append(c)
            print(f"  pairs>={mc}/{mo}, n>={mn}: {c['n_pairs']:>5} pairs | "
                  f"break {c['break_coors']:.2f} vs {c['break_other']:.2f} "
                  f"({c['break_ratio_pct']:.1f}%) | rho {c['rho_ratio_pct']:.1f}% | "
                  f"slope {c['slope_in_per_kgm3']:.1f} in per kg/m3")
    sl = [c["slope_in_per_kgm3"] for c in grid]
    R["coors_grid"] = grid
    R["coors_slope_range"] = [float(min(sl)), float(max(sl))]
    print(f"\n  BANKED CONSTANT WAS 19.3 (hard-coded, from filters 2/10/n>=3).")
    print(f"  regenerated range across defensible filters: {min(sl):.1f} to {max(sl):.1f} in per kg/m3")
    print(f"  -> the headline is filter-sensitive; report the RANGE, not the point.")

    json.dump(R, open(os.path.join(OUT, "roof_and_coors.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'roof_and_coors.json')}")


if __name__ == "__main__":
    main()
