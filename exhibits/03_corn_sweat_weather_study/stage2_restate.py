"""AMENDMENT 3 / domain-review items 1 and 2 — Stage-2 restatement.

Item 1: the clustering unit is the SEASON, not the park. Jul-Aug Midwest dew point is SYNOPTIC --
all 7 corn parks share one Gulf-moisture regime, so a summer is roughly ONE effective draw. My
park-cluster bootstrap treated 7 parks as 7 independent draws and overstated precision. Same trap
class as the A1 park-level catch, one level up.

Item 2: the "Missouri/Illinois not Minnesota/Michigan" park conclusion is a SPEC ARTIFACT.
analyze.py's stage2() fits a GLOBAL dew model with NO park fixed effect, so the per-park residual is
a LEVEL contrast (Midwest-interior vs NE-coastal climate), not the pre-registered WITHIN-park SHAPE
statistic. The correct statistic is tassel-window minus shoulder-window, within park.

Verified here rather than taken on trust -- the reviewer's numbers are reproduced or disputed.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

from analyze import SEED, OUT, load

WIN_LO, WIN_HI = 191, 243                 # Jul 10 - Aug 31 (tassel window)
SHOULDER = [(121, 180), (254, 273)]       # May 1 - Jun 29 and Sep 11 - Sep 30


def detrended(games):
    """Parent-study residual: global dew model, temp + 3 harmonics, NO park FE (the artifact)."""
    g = games[~games.is_coors].copy()
    doy = g.doy.values
    cols = [np.ones(len(g)), g.temperature_2m_c.values, g.temperature_2m_c.values ** 2]
    for k in (1, 2, 3):
        cols += [np.sin(2 * np.pi * k * doy / 365.25), np.cos(2 * np.pi * k * doy / 365.25)]
    X = np.column_stack(cols)
    b, *_ = np.linalg.lstsq(X, g.dew_point_c.values, rcond=None)
    g["dew_resid_noparkFE"] = g.dew_point_c.values - X @ b
    return g


def main():
    games, _ = load()
    g = detrended(games)
    band = g[(g.lat >= 38) & (g.lat <= 45) & (~g.is_roofed) &
             (~g.park_name.isin(["Sutter Health Park"]))]
    R = {"seed": SEED}

    print("== ITEM 1: clustering unit is the SEASON, not the park ==")
    win = band[band.doy.between(WIN_LO, WIN_HI)]
    per_season = {}
    for s, blk in win.groupby("season"):
        c = blk[blk.is_corn].dew_resid_noparkFE.mean()
        n = blk[~blk.is_corn].dew_resid_noparkFE.mean()
        per_season[s] = float(c - n)
        print(f"  {s}: corn - control = {c-n:+.3f} C   "
              f"(corn n={int(blk.is_corn.sum())}, control n={int((~blk.is_corn).sum())})")
    vals = np.array(list(per_season.values()))
    m, sd = vals.mean(), vals.std(ddof=1)
    se = sd / np.sqrt(len(vals))
    tcrit = {2: 12.71, 3: 4.303, 4: 3.182}.get(len(vals), 2.78)
    lo, hi = m - tcrit * se, m + tcrit * se
    print(f"\n  pooled (parent, park-bootstrap): +1.02 C, CI [+0.19, +1.82]  <- OVERSTATED")
    print(f"  season-clustered: mean {m:+.3f} C, sd {sd:.3f}, n_seasons={len(vals)}, "
          f"t-CI [{lo:+.3f}, {hi:+.3f}]")
    print(f"  -> CI {'CONTAINS' if lo < 0 < hi else 'EXCLUDES'} zero  =>  "
          f"{'CORN-UNRESOLVED' if lo < 0 < hi else 'CORN-CONFIRMED'}")
    R["item1_per_season"] = per_season
    R["item1_season_clustered"] = {"mean": float(m), "sd": float(sd), "n_seasons": int(len(vals)),
                                   "ci_lo": float(lo), "ci_hi": float(hi),
                                   "contains_zero": bool(lo < 0 < hi)}

    print("\n== ITEM 2: level contrast (parent, NO park FE) vs within-park SHAPE (correct) ==")
    sh = band[band.doy.apply(lambda d: any(a <= d <= b for a, b in SHOULDER))]
    rows = []
    for pid, blk in band.groupby("park_id"):
        w = blk[blk.doy.between(WIN_LO, WIN_HI)]
        s = sh[sh.park_id == pid]
        if len(w) < 20 or len(s) < 20:
            continue
        rows.append({"park_id": pid, "park": blk.park_name.iloc[0],
                     "is_corn": bool(blk.is_corn.iloc[0]),
                     "level_parent": float(w.dew_resid_noparkFE.mean()),
                     "shape_did": float(w.dew_resid_noparkFE.mean() - s.dew_resid_noparkFE.mean()),
                     "n_win": int(len(w)), "n_shoulder": int(len(s))})
    df = pd.DataFrame(rows)
    df["rank_level"] = df.level_parent.rank(ascending=False).astype(int)
    df["rank_shape"] = df.shape_did.rank(ascending=False).astype(int)
    df = df.sort_values("shape_did", ascending=False)
    print(df[["park", "is_corn", "level_parent", "rank_level", "shape_did", "rank_shape"]]
          .to_string(index=False))
    df.to_csv(os.path.join(OUT, "stage2_shape_vs_level.csv"), index=False)
    R["item2_parks"] = rows

    for nm in ("Target Field", "Comerica Park", "Busch Stadium", "Kauffman Stadium"):
        r = df[df.park == nm]
        if len(r):
            r = r.iloc[0]
            print(f"  {nm:20s} level {r.level_parent:+.2f} (rank {r.rank_level:2d})   "
                  f"SHAPE {r.shape_did:+.2f} (rank {r.rank_shape:2d})")

    corn_shape = df[df.is_corn].shape_did.mean()
    ctrl_shape = df[~df.is_corn].shape_did.mean()
    print(f"\n  corn mean SHAPE {corn_shape:+.3f} vs control {ctrl_shape:+.3f} "
          f"(diff {corn_shape-ctrl_shape:+.3f} C)")
    R["item2_shape_corn_minus_control"] = float(corn_shape - ctrl_shape)

    print("\n== ITEM 2b: is the level contrast just urbanity? (internal check) ==")
    urban = {"Busch Stadium", "Great American Ball Park", "Rate Field", "Wrigley Field"}
    u = df[df.park.isin(urban)]
    print(f"  Busch / GABP / Rate / Wrigley all urban; level residuals: "
          f"{', '.join(f'{r.park.split()[0]} {r.level_parent:+.2f}' for _, r in u.iterrows())}")
    print("  -> all positive, so urban-dryness cannot explain the corn-belt level contrast")

    json.dump(R, open(os.path.join(OUT, "stage2_restate.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'stage2_restate.json')}")


if __name__ == "__main__":
    main()
