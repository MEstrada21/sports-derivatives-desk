"""AMENDMENT 1 / A1 inference correction — CORN-LABEL permutation.

The DiD treatment (corn x Jul10-Aug31) varies at the PARK level and there are only 7 treated
open-air parks. Clustering the SE by GAME -- as measurement_gap.py does -- treats ~470 games as
independent draws and therefore UNDERSTATES the uncertainty badly. With 7 treated clusters,
cluster-robust asymptotics are unreliable too.

The exact, assumption-light null: randomly REASSIGN which parks are "corn" (keeping the count at 7)
and rebuild the interaction. Everything else -- the window, the weather controls, the fixed effects,
the real outcomes -- is untouched. The observed statistic is then referred to that distribution.
This is the honest inference for a 7-treated-cluster design.

Also runs the fit/held-out era split on the one endpoint that moved (release spin).
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

from analyze import SEED, OUT, load, absorb, dummies, wls_cluster, GAME_COLS

WIN_LO, WIN_HI = 191, 243
N_PERM = 300


def did_z(cells, games, mask, y_col, corn_parks, seasons=None):
    g = games[mask]
    if seasons is not None:
        g = g[g.season.isin(seasons)]
    d = cells.merge(g[GAME_COLS + ["doy"]], on="game_id", how="inner")
    d = d[d.n >= 3].dropna(subset=["break_mag", "velo", "spin"]).copy()
    d["corn_window"] = (d.park_id.isin(corn_parks) &
                        d.doy.between(WIN_LO, WIN_HI)).astype(float)
    if d.corn_window.sum() == 0:
        return np.nan, np.nan
    d["fe"] = d.pitcher_id + "|" + d.pitch_type.astype(str) + "|" + d.season
    reg = pd.DataFrame({"corn_window": d.corn_window.values, "rho_dry": d.rho_dry.values,
                        "vapor_deficit": d.vapor_density_deficit.values,
                        "temp": d.temperature_2m_c.values,
                        "temp2": d.temperature_2m_c.values ** 2,
                        "wind": d.wind_speed_10m_ms.values,
                        "precip": d.precipitation_mm.values})
    X = pd.concat([reg, dummies(d.park_id).reset_index(drop=True),
                   dummies(d.season_month).reset_index(drop=True)], axis=1)
    cols = list(X.columns)
    frame = pd.concat([pd.DataFrame({y_col: d[y_col].values, "fe": d.fe.values, "n": d.n.values}),
                       X], axis=1)
    dm = absorb(frame, [y_col] + cols, "fe", "n")
    res, _, _ = wls_cluster(dm[y_col].values, dm[cols].values, d.n.values, d.game_id.values, cols)
    b, se = res["corn_window"]
    return b, b / se


def main():
    games, cells = load()
    mask = ((~games.is_roofed) & (~games.is_coors)).values
    g = games[mask]
    real_corn = sorted(g[g.is_corn].park_id.unique().tolist())
    all_parks = sorted(g.park_id.unique().tolist())
    k = len(real_corn)
    print(f"open-air parks: {len(all_parks)}   real corn parks: {k}  -> "
          f"only {k} treated clusters, hence label permutation\n")

    R = {"seed": SEED, "n_perm": N_PERM, "n_corn_parks": k, "n_parks": len(all_parks),
         "real_corn_parks": real_corn, "endpoints": {}}

    rng = np.random.default_rng(SEED)
    draws = [sorted(rng.choice(all_parks, k, replace=False).tolist()) for _ in range(N_PERM)]

    for y in ("break_mag", "spin", "velo"):
        b_obs, z_obs = did_z(cells, games, mask, y, real_corn)
        betas = []
        for i, cp in enumerate(draws):
            bb, _ = did_z(cells, games, mask, y, cp)
            betas.append(bb)
            if (i + 1) % 100 == 0:
                print(f"  {y}: perm {i+1}/{N_PERM}", flush=True)
        betas = np.array([x for x in betas if np.isfinite(x)])
        p_two = float(np.mean(np.abs(betas) >= abs(b_obs)))
        pct = float((betas < b_obs).mean() * 100)
        R["endpoints"][y] = {
            "beta_observed": b_obs, "z_game_clustered_OVERSTATED": z_obs,
            "perm_mean": float(betas.mean()), "perm_sd": float(betas.std()),
            "perm_p_two_sided": p_two, "observed_percentile_in_null": pct,
            "z_vs_permutation_sd": float((b_obs - betas.mean()) / betas.std())}
        print(f"\n  {y:10s} observed beta={b_obs:+9.4f}  (game-clustered z={z_obs:+.2f} <- OVERSTATED)")
        print(f"  {'':10s} corn-label null: mean={betas.mean():+9.4f} sd={betas.std():.4f}"
              f"  -> honest z={(b_obs-betas.mean())/betas.std():+.2f}"
              f"   perm p={p_two:.3f}   observed sits at {pct:.1f}th pct\n")

    print("== era split on release spin (the one endpoint that moved) ==")
    for era, yrs in (("fit 2023-2024", ("2023", "2024")), ("held-out 2025-2026", ("2025", "2026"))):
        b, z = did_z(cells, games, mask, "spin", real_corn, seasons=yrs)
        R.setdefault("spin_era", {})[era] = {"beta": b, "z_game_clustered": z}
        print(f"  {era:20s} beta={b:+9.4f}  (game-clustered z={z:+.2f})")

    json.dump(R, open(os.path.join(OUT, "cell_permutation.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'cell_permutation.json')}")


if __name__ == "__main__":
    main()
