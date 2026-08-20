"""AMENDMENT 3 — extract spin AXIS (and release-consistency) cells from the pitch archive.

Both reviewers independently named the spin-axis test as the decisive experiment for identifying
the non-aerodynamic humidity channel. Data is already on disk (`spin_axis_degrees`, 99-100%
populated); no new pull.

Spin axis is CIRCULAR, so it cannot be averaged directly. Per (game, pitcher, pitch_type) cell we
carry the two linear components mean(sin), mean(cos) -- each regressable -- plus the resultant
length R = hypot(mean_sin, mean_cos), which measures RELEASE CONSISTENCY (R=1 all pitches identical
axis, R->0 scattered). Grip failure should scatter the axis (R falls); a change in the ball's
surface aerodynamics should not touch release kinematics at all.
"""
from __future__ import annotations
import argparse, glob, os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

LANE = os.path.dirname(os.path.abspath(__file__))
# DATA_ROOT must contain data/backfill/{pitch,plate_appearance}/ parquet archives built
# from the public MLB StatsAPI game feeds. Default: a data/ tree next to these scripts.
ROOT = os.environ.get("DATA_ROOT", LANE)
OUT = os.path.join(LANE, "out")


def _one(f: str):
    cols = ["game_id", "plate_appearance_id", "pitch_type", "spin_axis_degrees",
            "spin_rate_rpm", "horizontal_break_inches", "vertical_break_inches", "velocity_mph"]
    try:
        d = pd.read_parquet(f, columns=cols)
    except Exception:
        return None
    if d.empty:
        return None
    for c in cols[3:]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["spin_axis_degrees", "spin_rate_rpm", "horizontal_break_inches",
                         "vertical_break_inches"])
    if d.empty:
        return None
    d["game_id"] = d.game_id.astype(str)
    th = np.deg2rad(d.spin_axis_degrees.values)
    d["ax_sin"], d["ax_cos"] = np.sin(th), np.cos(th)
    d["break_mag"] = np.hypot(d.horizontal_break_inches, d.vertical_break_inches)
    # inches of break per 1000 rpm = spin EFFICIENCY proxy (aerodynamic response per unit spin)
    d["eff"] = d.break_mag / np.clip(d.spin_rate_rpm, 1, None) * 1000.0

    pa_dir = os.path.dirname(f).replace("/backfill/pitch/", "/backfill/plate_appearance/")
    pas = sorted(glob.glob(os.path.join(pa_dir, "*.parquet")))
    if not pas:
        return None
    pa = pd.concat([pd.read_parquet(p, columns=["plate_appearance_id", "pitcher_id"])
                    for p in pas], ignore_index=True)
    pa["pitcher_id"] = pa.pitcher_id.astype(str)
    d = d.merge(pa.drop_duplicates("plate_appearance_id"), on="plate_appearance_id", how="inner")
    if d.empty:
        return None
    g = d.groupby(["game_id", "pitcher_id", "pitch_type"], observed=True).agg(
        n=("ax_sin", "size"), ax_sin=("ax_sin", "mean"), ax_cos=("ax_cos", "mean"),
        eff=("eff", "mean"), break_mag=("break_mag", "mean"), spin=("spin_rate_rpm", "mean"),
        velo=("velocity_mph", "mean")).reset_index()
    g["R"] = np.hypot(g.ax_sin, g.ax_cos)          # release-axis consistency
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    dest = os.path.join(OUT, "axis_cells.parquet")
    if os.path.exists(dest) and not args.force:
        print(f"SKIP (exists): {dest}")
        return
    files = sorted(glob.glob(os.path.join(ROOT, "data/backfill/pitch/**/*.parquet"),
                            recursive=True))
    print(f"pitch files: {len(files)}", flush=True)
    parts = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for i, r in enumerate(ex.map(_one, files, chunksize=64)):
            if r is not None:
                parts.append(r)
            if i % 2000 == 0:
                print(f"  ..{i}/{len(files)}", flush=True)
    df = pd.concat(parts, ignore_index=True)
    df.to_parquet(dest, index=False)
    print(f"WROTE {dest} cells={len(df)} pitches={int(df.n.sum())}")


if __name__ == "__main__":
    main()
