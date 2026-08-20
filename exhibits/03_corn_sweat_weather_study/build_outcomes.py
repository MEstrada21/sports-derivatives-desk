"""Stage 0b: extract outcome aggregates from the PA + pitch archives.

  out/game_pa.parquet    : game_id -> BIP, HR, K, BB, PA (+ early/late split)
  out/pitch_cells.parquet: (game_id, pitcher_id, pitch_type) -> n, mean break/velo/spin

Cells are the right reduction for a GAME-LEVEL regressor: air density is constant within a game,
so collapsing to cells loses no information about beta_rho while making pitcher x pitch_type fixed
effects tractable (FWL demeaning on ~500k cells instead of ~2.5M pitches).

Idempotent; parallel over 8 cores. Works around task #46 (game_id str/int32 hive collision) by
reading each file explicitly with a column projection rather than a dataset scan.
"""
from __future__ import annotations
import argparse, glob, os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

LANE = os.path.dirname(os.path.abspath(__file__))
# DATA_ROOT must contain data/backfill/{plate_appearance,pitch}/ parquet archives built
# from the public MLB StatsAPI game feeds. Default: a data/ tree next to these scripts.
ROOT = os.environ.get("DATA_ROOT", LANE)
OUT = os.path.join(LANE, "out")

NON_BIP = {"strikeout", "strikeout_double_play", "walk", "intent_walk", "hit_by_pitch",
           "catcher_interf", "batter_interference", "sac_bunt", "sac_bunt_double_play",
           "ejection", "game_advisory", "runner_double_play", "pickoff_1b", "pickoff_2b",
           "pickoff_3b", "caught_stealing_2b", "caught_stealing_3b", "caught_stealing_home",
           "stolen_base_2b", "stolen_base_3b", "other_out", "passed_ball", "wild_pitch",
           "balk", "defensive_indiff", "runner_placed"}
K_EV = {"strikeout", "strikeout_double_play"}
BB_EV = {"walk", "intent_walk"}


def _pa_file(f: str):
    try:
        d = pd.read_parquet(f, columns=["game_id", "game_date", "play_event", "inning", "park_id"])
    except Exception:
        return None
    if d.empty:
        return None
    ev = d.play_event.astype(str)
    bip = ~ev.isin(NON_BIP)
    hr = ev.eq("home_run")
    late = d.inning.astype(int) >= 6
    return {
        "game_id": str(d.game_id.iloc[0]),
        "game_date": str(d.game_date.iloc[0]),
        "park_id": str(d.park_id.iloc[0]),
        "pa": int(len(d)),
        "bip": int(bip.sum()),
        "hr": int(hr.sum()),
        "k": int(ev.isin(K_EV).sum()),
        "bb": int(ev.isin(BB_EV).sum()),
        "bip_early": int((bip & ~late).sum()),
        "hr_early": int((hr & ~late).sum()),
        "bip_late": int((bip & late).sum()),
        "hr_late": int((hr & late).sum()),
    }


def _pitch_file(f: str):
    """pitcher_id lives on the PA table, not the pitch table -- join via plate_appearance_id."""
    cols = ["game_id", "plate_appearance_id", "pitch_type", "velocity_mph", "spin_rate_rpm",
            "horizontal_break_inches", "vertical_break_inches"]
    try:
        d = pd.read_parquet(f, columns=cols)
    except Exception:
        return None
    if d.empty:
        return None
    d["game_id"] = d.game_id.astype(str)
    for c in ["velocity_mph", "spin_rate_rpm", "horizontal_break_inches", "vertical_break_inches"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["horizontal_break_inches", "vertical_break_inches", "velocity_mph"])
    if d.empty:
        return None
    d["break_mag"] = np.hypot(d.horizontal_break_inches, d.vertical_break_inches)

    pa_dir = os.path.dirname(f).replace("/backfill/pitch/", "/backfill/plate_appearance/")
    pa_files = sorted(glob.glob(os.path.join(pa_dir, "*.parquet")))
    if not pa_files:
        return None
    pa = pd.concat([pd.read_parquet(p, columns=["plate_appearance_id", "pitcher_id"])
                    for p in pa_files], ignore_index=True)
    pa["pitcher_id"] = pa.pitcher_id.astype(str)
    pa = pa.drop_duplicates("plate_appearance_id")
    d = d.merge(pa, on="plate_appearance_id", how="inner")
    if d.empty:
        return None
    g = d.groupby(["game_id", "pitcher_id", "pitch_type"], observed=True).agg(
        n=("break_mag", "size"), break_mag=("break_mag", "mean"),
        ivb=("vertical_break_inches", "mean"), hb=("horizontal_break_inches", "mean"),
        velo=("velocity_mph", "mean"), spin=("spin_rate_rpm", "mean")).reset_index()
    return g


def run(files, fn, workers=8, chunk=64):
    res = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(fn, files, chunksize=chunk)):
            if r is not None:
                res.append(r)
            if i % 2000 == 0:
                print(f"  ..{i}/{len(files)}", flush=True)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    pa_dest = os.path.join(OUT, "game_pa.parquet")
    if args.force or not os.path.exists(pa_dest):
        files = sorted(glob.glob(os.path.join(ROOT, "data/backfill/plate_appearance/**/*.parquet"),
                                recursive=True))
        print(f"PA files: {len(files)}")
        rows = run(files, _pa_file)
        df = pd.DataFrame(rows)
        # a game can appear in >1 file (corrections); sum then dedupe defensively
        df = df.groupby(["game_id", "game_date", "park_id"], as_index=False).max(numeric_only=True)
        df.to_parquet(pa_dest, index=False)
        print(f"WROTE {pa_dest} rows={len(df)}")
    else:
        print(f"SKIP (exists): {pa_dest}")

    pc_dest = os.path.join(OUT, "pitch_cells.parquet")
    if args.force or not os.path.exists(pc_dest):
        files = sorted(glob.glob(os.path.join(ROOT, "data/backfill/pitch/**/*.parquet"),
                                recursive=True))
        print(f"pitch files: {len(files)}")
        parts = run(files, _pitch_file)
        df = pd.concat(parts, ignore_index=True)
        df = df.groupby(["game_id", "pitcher_id", "pitch_type"], as_index=False).agg(
            n=("n", "sum"), break_mag=("break_mag", "mean"), ivb=("ivb", "mean"),
            hb=("hb", "mean"), velo=("velo", "mean"), spin=("spin", "mean"))
        df.to_parquet(pc_dest, index=False)
        print(f"WROTE {pc_dest} cells={len(df)} pitches={int(df.n.sum())}")
    else:
        print(f"SKIP (exists): {pc_dest}")


if __name__ == "__main__":
    main()
