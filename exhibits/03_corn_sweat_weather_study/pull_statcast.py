"""AMENDMENT 2 — Statcast batted-ball pull (operator-approved 2026-08-09).

Idempotent per-day parquet cache inside this lane only. Resumable: re-running skips days already
cached, so an interrupted pull costs nothing. Polite: each Savant day-query already takes ~8s
(≈7 req/min) and we add an explicit inter-request sleep on top.

Only batted balls with a measured distance are retained, and only the columns the pre-registered
spec needs -- the cache stays small and the raw pull is not hoarded.

Provenance for the manifest: pybaseball version, pull timestamps, per-day row counts.
"""
from __future__ import annotations
import argparse, json, os, time, warnings
from datetime import date, timedelta

warnings.filterwarnings("ignore")
import pandas as pd

LANE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(LANE, "cache", "statcast")
OUT = os.path.join(LANE, "out")

KEEP = ["game_pk", "game_date", "game_type", "launch_speed", "launch_angle", "hit_distance_sc",
        "bb_type", "events", "description", "home_team", "inning", "batter", "pitcher",
        "stand", "p_throws"]

# Mar 15 - Oct 15 each season (skips the offseason instead of burning empty requests);
# 2026 ends at the parent corpus boundary.
WINDOWS = [("2023-03-15", "2023-10-15"), ("2024-03-15", "2024-10-15"),
           ("2025-03-15", "2025-10-15"), ("2026-03-15", "2026-07-02")]


def daterange(a: str, b: str):
    d0 = date.fromisoformat(a); d1 = date.fromisoformat(b)
    while d0 <= d1:
        yield d0.isoformat()
        d0 += timedelta(days=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    os.makedirs(CACHE, exist_ok=True)

    import pybaseball
    from pybaseball import statcast
    ver = pybaseball.__version__

    days = [d for w in WINDOWS for d in daterange(*w)]
    todo = [d for d in days if args.force or not os.path.exists(os.path.join(CACHE, f"{d}.parquet"))]
    print(f"pybaseball {ver} | {len(days)} candidate days | {len(todo)} to pull "
          f"| {len(days)-len(todo)} already cached", flush=True)

    started = pd.Timestamp.utcnow().isoformat()
    n_new = 0
    for i, d in enumerate(todo):
        dest = os.path.join(CACHE, f"{d}.parquet")
        try:
            raw = statcast(start_dt=d, end_dt=d, verbose=False)
        except Exception as e:
            print(f"  {d}: ERROR {type(e).__name__}: {e}", flush=True)
            time.sleep(5.0)
            continue
        if raw is None or len(raw) == 0:
            pd.DataFrame(columns=KEEP).to_parquet(dest, index=False)
        else:
            cols = [c for c in KEEP if c in raw.columns]
            sub = raw[cols].copy()
            sub = sub[sub.hit_distance_sc.notna()]
            for c in ["launch_speed", "launch_angle", "hit_distance_sc"]:
                if c in sub.columns:
                    sub[c] = pd.to_numeric(sub[c], errors="coerce")
            sub["game_pk"] = sub.game_pk.astype(str)
            sub.to_parquet(dest, index=False)
        n_new += 1
        if n_new % 25 == 0:
            print(f"  ..{n_new}/{len(todo)} pulled (latest {d})", flush=True)
        time.sleep(args.sleep)

    files = sorted(f for f in os.listdir(CACHE) if f.endswith(".parquet"))
    total = 0
    for f in files:
        try:
            total += len(pd.read_parquet(os.path.join(CACHE, f), columns=["game_pk"]))
        except Exception:
            pass
    man = {"pybaseball_version": ver, "source": "Baseball Savant via pybaseball.statcast",
           "pull_started_utc": started, "pull_finished_utc": pd.Timestamp.utcnow().isoformat(),
           "windows": WINDOWS, "n_days_cached": len(files), "n_batted_balls_cached": total,
           "columns_kept": KEEP,
           "note": "batted balls with non-null hit_distance_sc only; per-day idempotent cache"}
    json.dump(man, open(os.path.join(OUT, "statcast_manifest.json"), "w"), indent=2)
    print(json.dumps(man, indent=2), flush=True)


if __name__ == "__main__":
    main()
