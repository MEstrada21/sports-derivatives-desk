"""Corn-sweat study, SPEC v2. Stages 1A / 1B / 2 + full control battery.

SPEC v1 (out/results_specv1_CONFOUNDED.json) FAILED its own pre-registered controls: the
permutation null did not centre on zero (1A permuted beta=+6.17, z=+23.9) and the release-velocity
placebo was strongly non-zero (z=-30.8). Both had the same cause -- no month fixed effects, so
seasonal temperature was masquerading as air density. v2 fixes identification:

  * season x month fixed effects added (identification is now WITHIN park, WITHIN calendar month)
  * temperature + temperature^2 entered explicitly, so density coefficients are TEMPERATURE-PURGED
  * the key regressors are the two BEHAVIOURALLY-INERT density channels:
        vapor_density_deficit  = density removed by water vapour (the corn-sweat channel)
        rho_dry (temp-purged)  = density from barometric pressure
    A pitcher's muscles respond to heat; they do not respond to barometric pressure or to the
    partial pressure of water vapour. Any effect on these two channels is aerodynamics, not
    behaviour.

The respecification was driven by FAILED CONTROLS, not by the headline number; both specs are
reported in LEDGER.md.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

SEED = 20260809
LANE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(LANE, "out")

# Coors natural-experiment calibration (same pitchers, 919 pitcher x pitch-type pairs):
# density 0.9884 vs 1.1704 (-15.5%), break 11.55 vs 15.07 (-23.4%)  ->  ~19.3 in per kg/m3
COORS_SLOPE_IN_PER_KGM3 = (15.070 - 11.551) / (1.17045 - 0.98844)


# ---------------------------------------------------------------- linear algebra

def wls_cluster(y, X, w, cluster, names):
    y = np.asarray(y, float); X = np.asarray(X, float); w = np.asarray(w, float)
    sw = np.sqrt(w)
    Xw, yw = X * sw[:, None], y * sw
    XtX_inv = np.linalg.pinv(Xw.T @ Xw)
    beta = XtX_inv @ (Xw.T @ yw)
    resid = yw - Xw @ beta
    cl = pd.factorize(cluster)[0]
    G = cl.max() + 1
    agg = np.zeros((G, X.shape[1]))
    np.add.at(agg, cl, Xw * resid[:, None])
    n, k = X.shape
    dfc = (G / (G - 1)) * ((n - 1) / max(n - k, 1))
    V = XtX_inv @ (agg.T @ agg) @ XtX_inv * dfc
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    return {nm: (float(beta[i]), float(se[i])) for i, nm in enumerate(names)}, beta, V


def absorb(df, cols, group, weights):
    w = df[weights].values
    key, _ = pd.factorize(df[group].values)
    wsum = np.bincount(key, weights=w)
    out = pd.DataFrame(index=df.index)
    for c in cols:
        gm = np.bincount(key, weights=w * df[c].values) / np.clip(wsum, 1e-12, None)
        out[c] = df[c].values - gm[key]
    return out


def dummies(s):
    return pd.get_dummies(s.astype(str), prefix="d", drop_first=True).astype(float)


def linear_combo(beta, V, cols, spec):
    c = np.zeros(len(cols))
    for name, mult in spec.items():
        c[cols.index(name)] = mult
    s = float(c @ beta); se = float(np.sqrt(max(c @ V @ c, 0.0)))
    return s, se, (s / se if se > 0 else float("nan"))


# ---------------------------------------------------------------- data

def load():
    gw = pd.read_parquet(os.path.join(OUT, "game_weather.parquet"))
    pa = pd.read_parquet(os.path.join(OUT, "game_pa.parquet"))
    gw["game_id"] = gw.game_id.astype(str); pa["game_id"] = pa.game_id.astype(str)
    g = gw.merge(pa.drop(columns=["game_date", "park_id"]), on="game_id", how="inner")
    g["season_month"] = g.season + "-" + g.month
    cells = pd.read_parquet(os.path.join(OUT, "pitch_cells.parquet"))
    cells["game_id"] = cells.game_id.astype(str)
    for c in ["break_mag", "velo", "spin", "n"]:
        cells[c] = pd.to_numeric(cells[c], errors="coerce")
    cells = cells.dropna(subset=["break_mag", "velo", "n"])
    return g, cells


GAME_COLS = ["game_id", "park_id", "season", "season_month", "rho", "rho_dry",
             "vapor_density_deficit", "temperature_2m_c", "dew_point_c", "surface_pressure_hpa",
             "wind_speed_10m_ms", "precipitation_mm", "is_coors"]

PERM_COLS = ["rho", "rho_dry", "vapor_density_deficit", "temperature_2m_c", "dew_point_c",
             "surface_pressure_hpa", "wind_speed_10m_ms", "precipitation_mm"]


def permute_within(frame, games, rng, cols=PERM_COLS):
    """Reassign whole weather vectors across games within park x calendar-month strata."""
    gm = games[["game_id", "park_id", "month"] + cols].drop_duplicates("game_id")
    parts = []
    for _, blk in gm.groupby(["park_id", "month"], sort=True):
        b = blk.copy()
        b[cols] = b[cols].values[rng.permutation(len(b))]
        parts.append(b)
    sh = pd.concat(parts, ignore_index=True)[["game_id"] + cols]
    return frame.drop(columns=[c for c in cols if c in frame.columns]).merge(sh, on="game_id")


# ---------------------------------------------------------------- STAGE 1A

def stage1a(cells, games, mask, y_col="break_mag", label="", rng=None, planted_slope=0.0):
    g = games[mask]
    d = cells.merge(g[GAME_COLS], on="game_id", how="inner")
    d = d[d.n >= 3].copy()
    if rng is not None:
        d = permute_within(d, games, rng)
    if planted_slope:
        d[y_col] = d[y_col] + planted_slope * (d.vapor_density_deficit - d.vapor_density_deficit.mean())
    d["fe"] = d.pitcher_id + "|" + d.pitch_type.astype(str) + "|" + d.season

    reg = pd.DataFrame({
        "rho_dry": d.rho_dry.values,
        "vapor_deficit": d.vapor_density_deficit.values,
        "temp": d.temperature_2m_c.values,
        "temp2": d.temperature_2m_c.values ** 2,
        "wind": d.wind_speed_10m_ms.values,
        "precip": d.precipitation_mm.values,
    })
    X = pd.concat([reg, dummies(d.park_id).reset_index(drop=True),
                   dummies(d.season_month).reset_index(drop=True)], axis=1)
    cols = list(X.columns)
    frame = pd.concat([pd.DataFrame({y_col: d[y_col].values, "fe": d.fe.values,
                                     "n": d.n.values}), X], axis=1)
    dm = absorb(frame, [y_col] + cols, "fe", "n")
    res, beta, V = wls_cluster(dm[y_col].values, dm[cols].values, d.n.values, d.game_id.values, cols)
    # a kg/m3 is a kg/m3: vapour effect should be MINUS the pressure effect
    s, s_se, s_z = linear_combo(beta, V, cols, {"rho_dry": 1.0, "vapor_deficit": 1.0})
    return {"label": label, "y": y_col, "n_pitches": int(d.n.sum()),
            "n_games": int(d.game_id.nunique()), "n_cells": int(len(d)),
            "mean_y": float(np.average(d[y_col], weights=d.n)),
            "beta_pressure_channel": res["rho_dry"][0], "se_pressure_channel": res["rho_dry"][1],
            "beta_vapor_channel": res["vapor_deficit"][0], "se_vapor_channel": res["vapor_deficit"][1],
            "z_pressure": res["rho_dry"][0] / res["rho_dry"][1],
            "z_vapor": res["vapor_deficit"][0] / res["vapor_deficit"][1],
            "sum_equal_and_opposite": s, "se_sum": s_se, "z_sum": s_z,
            "beta_temp": res["temp"][0], "se_temp": res["temp"][1]}


# ---------------------------------------------------------------- STAGE 1B

def stage1b(games, mask, label="", y_num="hr", y_den="bip", key="dew_point_c",
            rng=None, planted_pp_per_unit=0.0):
    g = games[mask].copy()
    g = g[(g[y_den] > 0) & (~g.is_coors)]
    if rng is not None:
        g = permute_within(g, games, rng)
    y = g[y_num].values / g[y_den].values
    if planted_pp_per_unit:
        y = y + (planted_pp_per_unit / 100.0) * (g[key].values - g[key].values.mean())
    reg = pd.DataFrame({key: g[key].values,
                        "temp": g.temperature_2m_c.values,
                        "temp2": g.temperature_2m_c.values ** 2,
                        "wind": g.wind_speed_10m_ms.values,
                        "precip": g.precipitation_mm.values, "const": 1.0})
    if key != "dew_point_c":
        pass
    X = pd.concat([reg, dummies(g.park_id).reset_index(drop=True),
                   dummies(g.season_month).reset_index(drop=True)], axis=1)
    res, beta, V = wls_cluster(y, X.values, g[y_den].values, g.game_id.values, list(X.columns))
    b, se = res[key]
    return {"label": label, "key": key, "n_games": int(len(g)), "n_bip": int(g[y_den].sum()),
            "n_hr": int(g[y_num].sum()),
            "base_rate_pp": float(100 * g[y_num].sum() / g[y_den].sum()),
            "beta_pp": 100 * b, "se_pp": 100 * se,
            "ci_lo_pp": 100 * (b - 1.96 * se), "ci_hi_pp": 100 * (b + 1.96 * se)}


# ---------------------------------------------------------------- STAGE 2

def stage2(games, drop_parks=(), label=""):
    g = games[~games.is_coors].copy()
    doy = g.doy.values
    cols = [np.ones(len(g)), g.temperature_2m_c.values, g.temperature_2m_c.values ** 2]
    for k in (1, 2, 3):
        cols += [np.sin(2 * np.pi * k * doy / 365.25), np.cos(2 * np.pi * k * doy / 365.25)]
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, g.dew_point_c.values, rcond=None)
    g["dew_resid"] = g.dew_point_c.values - X @ beta

    win = g[(g.doy >= 191) & (g.doy <= 243) & (g.lat >= 38) & (g.lat <= 45) & (~g.is_roofed)]
    win = win[~win.park_name.isin(drop_parks)]
    corn, non = win[win.is_corn], win[~win.is_corn]
    diff = corn.dew_resid.mean() - non.dew_resid.mean()
    rng = np.random.default_rng(SEED)
    cp, npk = corn.park_id.unique(), non.park_id.unique()
    cm = {p: corn[corn.park_id == p].dew_resid.mean() for p in cp}
    nm = {p: non[non.park_id == p].dew_resid.mean() for p in npk}
    boots = [np.mean([cm[p] for p in rng.choice(cp, len(cp), True)]) -
             np.mean([nm[p] for p in rng.choice(npk, len(npk), True)]) for _ in range(4000)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"label": label, "diff_c": float(diff), "ci_lo_c": float(lo), "ci_hi_c": float(hi),
            "n_corn_games": int(len(corn)), "n_non_games": int(len(non)),
            "n_corn_parks": int(len(cp)), "n_non_parks": int(len(npk)),
            "non_parks": sorted(non.park_name.unique().tolist())}, g


def main():
    games, cells = load()
    open_mask = (~games.is_roofed) & (~games.is_coors)
    roof_mask = games.is_roofed.values
    R = {"spec": "v2", "prereg_sha256": open(os.path.join(OUT, "PREREG_HASH.txt")).read().split()[0],
         "seed": SEED, "coors_calibration_in_per_kgm3": COORS_SLOPE_IN_PER_KGM3,
         "n_games": int(len(games)), "n_pitches": int(cells.n.sum())}

    print("== STAGE 1A: break as a barometer (temperature-purged density channels) ==")
    print(f"   physics benchmark from the Coors natural experiment: "
          f"{COORS_SLOPE_IN_PER_KGM3:.1f} inches of break per kg/m3\n")
    runs = [("s1a_primary", open_mask, "break_mag", "PRIMARY open-air ex-Coors"),
            ("s1a_roof_placebo", roof_mask, "break_mag", "ROOFED placebo"),
            ("s1a_velo_placebo", open_mask, "velo", "release-velocity placebo"),
            ("s1a_spin_placebo", open_mask, "spin", "release-spin placebo")]
    for k, m, y, lab in runs:
        R[k] = stage1a(cells, games, m, y_col=y, label=lab)
        r = R[k]
        print(f"  {lab:28s} y={y:9s}  pressure-ch {r['beta_pressure_channel']:+8.2f}"
              f" (z={r['z_pressure']:+6.1f})   vapour-ch {r['beta_vapor_channel']:+9.2f}"
              f" (z={r['z_vapor']:+6.1f})   equal&opp z={r['z_sum']:+6.1f}")

    R["s1a_perm"] = stage1a(cells, games, open_mask, label="permutation null",
                            rng=np.random.default_rng(SEED + 7))
    r = R["s1a_perm"]
    print(f"  {'PERMUTATION NULL':28s}            pressure-ch {r['beta_pressure_channel']:+8.2f}"
          f" (z={r['z_pressure']:+6.1f})   vapour-ch {r['beta_vapor_channel']:+9.2f}"
          f" (z={r['z_vapor']:+6.1f})")

    R["s1a_planted"] = []
    for dose in (COORS_SLOPE_IN_PER_KGM3, 2 * COORS_SLOPE_IN_PER_KGM3):
        pr = stage1a(cells, games, open_mask, planted_slope=dose, label=f"planted {dose:.1f}")
        net = pr["beta_vapor_channel"] - R["s1a_primary"]["beta_vapor_channel"]
        R["s1a_planted"].append({"dose": dose, "recovered_net": net,
                                 "se": pr["se_vapor_channel"],
                                 "recovery_ratio": net / dose})
        print(f"  planted vapour slope {dose:+7.2f} -> recovered net {net:+7.2f} "
              f"(ratio {net/dose:.3f}, se {pr['se_vapor_channel']:.2f})")

    print("\n== STAGE 1B: HR per batted ball ==")
    b_runs = [("s1b_primary", open_mask, "hr", "bip", "dew_point_c", "PRIMARY beta_dew"),
              ("s1b_roof_placebo", roof_mask, "hr", "bip", "dew_point_c", "ROOFED placebo"),
              ("s1b_vapor", open_mask, "hr", "bip", "vapor_density_deficit", "vapour-density channel"),
              ("s1b_k_placebo", open_mask, "k", "pa", "dew_point_c", "K-per-PA placebo"),
              ("s1b_bb_placebo", open_mask, "bb", "pa", "dew_point_c", "BB-per-PA placebo"),
              ("s1b_early", open_mask, "hr_early", "bip_early", "dew_point_c", "early innings 1-5"),
              ("s1b_late", open_mask, "hr_late", "bip_late", "dew_point_c", "late innings 6+")]
    for k, m, yn, yd, key, lab in b_runs:
        R[k] = stage1b(games, m, label=lab, y_num=yn, y_den=yd, key=key)
        r = R[k]
        print(f"  {lab:24s} beta={r['beta_pp']:+9.5f} pp/unit  se={r['se_pp']:.5f}  "
              f"95%CI=[{r['ci_lo_pp']:+.5f},{r['ci_hi_pp']:+.5f}]  base={r['base_rate_pp']:5.2f}pp")

    perms = [stage1b(games, open_mask, rng=np.random.default_rng(SEED + i))["beta_pp"]
             for i in range(300)]
    obs = R["s1b_primary"]["beta_pp"]
    R["s1b_perm"] = {"n": 300, "mean": float(np.mean(perms)), "sd": float(np.std(perms)),
                     "observed": obs,
                     "perm_p_two_sided": float(np.mean(np.abs(perms) >= abs(obs)))}
    print(f"  PERMUTATION NULL n=300: mean={R['s1b_perm']['mean']:+.5f} "
          f"sd={R['s1b_perm']['sd']:.5f}  obs={obs:+.5f}  perm_p={R['s1b_perm']['perm_p_two_sided']:.3f}")

    R["s1b_planted"] = []
    for dose in (0.008, 0.020, 0.040, 0.100):
        pr = stage1b(games, open_mask, planted_pp_per_unit=dose, label=f"planted {dose}")
        net = pr["beta_pp"] - obs
        rec = {"dose_pp_per_c": dose, "recovered_net_pp_per_c": net, "se_pp": pr["se_pp"],
               "ci_lo": pr["ci_lo_pp"], "ci_hi": pr["ci_hi_pp"],
               "ci_excludes_zero": bool(pr["ci_lo_pp"] > 0 or pr["ci_hi_pp"] < 0),
               "recovery_ratio": net / dose}
        R["s1b_planted"].append(rec)
        print(f"  planted {dose:+.3f} pp/C -> recovered net {net:+.5f} (ratio {net/dose:.3f})  "
              f"CI=[{rec['ci_lo']:+.5f},{rec['ci_hi']:+.5f}]  excl0={rec['ci_excludes_zero']}")

    print("\n== STAGE 2: corn signature ==")
    s2a, gg = stage2(games, label="all latitude-matched open-air parks")
    s2b, _ = stage2(games, drop_parks=("Sutter Health Park",),
                    label="ex Sutter Health Park (arid Sacramento outlier)")
    R["stage2_all"], R["stage2_ex_sutter"] = s2a, s2b
    for s in (s2a, s2b):
        print(f"  {s['label']:44s} diff={s['diff_c']:+.3f} C  "
              f"95%CI=[{s['ci_lo_c']:+.3f},{s['ci_hi_c']:+.3f}]  "
              f"({s['n_corn_parks']} corn vs {s['n_non_parks']} non-corn parks)")
    pp = (gg[(gg.doy >= 191) & (gg.doy <= 243) & (~gg.is_roofed)]
          .groupby(["park_id", "park_name", "state", "is_corn"])
          .dew_resid.agg(["mean", "size"]).reset_index().sort_values("mean", ascending=False))
    pp.to_csv(os.path.join(OUT, "stage2_park_residuals.csv"), index=False)
    print(pp.to_string(index=False))

    json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'results.json')}")


if __name__ == "__main__":
    main()
