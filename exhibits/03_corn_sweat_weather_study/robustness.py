"""Robustness: is the vapour-channel effect just temperature mis-specification?

vapor_density_deficit ~ RH * e_s(T), and e_s(T) is EXPONENTIAL in temperature. Controlling
temperature with a quadratic therefore leaves curvature that the vapour variable can absorb. The
measured humid -> less release spin also runs OPPOSITE to the stated expectation in the physics
literature (Nathan: better grip when humid should mean MORE spin), which is exactly the situation
where a second look is mandatory.

R1 replaces temp + temp^2 with 1-degC temperature BIN fixed effects -- fully nonparametric in
temperature. If the vapour coefficient survives, it is not temperature mis-specification.
R2 uses relative humidity instead of absolute vapour density (folk "feel" is RH; physics is
absolute vapour content).
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd

from analyze import SEED, OUT, load, absorb, dummies, wls_cluster, linear_combo, GAME_COLS


def fit(cells, games, mask, y_col, temp_ctrl="quad", hum="vapor", label="", drop_spin=False):
    g = games[mask]
    d = cells.merge(g[GAME_COLS + ["relative_humidity_2m_pct"]], on="game_id", how="inner")
    d = d[d.n >= 3].dropna(subset=["break_mag", "velo", "spin"]).copy()
    d["fe"] = d.pitcher_id + "|" + d.pitch_type.astype(str) + "|" + d.season

    hum_col = {"vapor": d.vapor_density_deficit.values,
               "rh": d.relative_humidity_2m_pct.values,
               "dew": d.dew_point_c.values}[hum]
    reg = {"rho_dry": d.rho_dry.values, "hum": hum_col,
           "wind": d.wind_speed_10m_ms.values, "precip": d.precipitation_mm.values}
    blocks = [pd.DataFrame(reg)]
    if temp_ctrl == "quad":
        blocks[0]["temp"] = d.temperature_2m_c.values
        blocks[0]["temp2"] = d.temperature_2m_c.values ** 2
    elif temp_ctrl == "bins":
        tb = pd.cut(d.temperature_2m_c, bins=np.arange(-5, 46, 1))
        blocks.append(dummies(tb.astype(str)).reset_index(drop=True))
    blocks += [dummies(d.park_id).reset_index(drop=True),
               dummies(d.season_month).reset_index(drop=True)]
    X = pd.concat([b.reset_index(drop=True) for b in blocks], axis=1)
    cols = list(X.columns)
    frame = pd.concat([pd.DataFrame({y_col: d[y_col].values, "fe": d.fe.values, "n": d.n.values}),
                       X], axis=1)
    dm = absorb(frame, [y_col] + cols, "fe", "n")
    res, beta, V = wls_cluster(dm[y_col].values, dm[cols].values, d.n.values, d.game_id.values, cols)
    s, se, z = linear_combo(beta, V, cols, {"rho_dry": 1.0, "hum": 1.0}) if hum == "vapor" \
        else (np.nan, np.nan, np.nan)
    return {"label": label, "y": y_col, "temp_ctrl": temp_ctrl, "humidity_var": hum,
            "n_pitches": int(d.n.sum()), "n_temp_bins": int(X.shape[1] - len(reg)) if temp_ctrl == "bins" else 0,
            "beta_pressure": res["rho_dry"][0], "se_pressure": res["rho_dry"][1],
            "z_pressure": res["rho_dry"][0] / res["rho_dry"][1],
            "beta_hum": res["hum"][0], "se_hum": res["hum"][1],
            "z_hum": res["hum"][0] / res["hum"][1],
            "z_equal_and_opposite": z}


def main():
    games, cells = load()
    m = ((~games.is_roofed) & (~games.is_coors)).values
    R = {"seed": SEED}

    print("== R1: quadratic temperature control vs NONPARAMETRIC 1-degC temperature bins ==\n")
    print(f"{'endpoint':10s} {'temp control':14s} {'pressure ch':>22s} {'humidity ch':>24s}")
    for y in ("break_mag", "spin", "velo"):
        for tc in ("quad", "bins"):
            r = fit(cells, games, m, y, temp_ctrl=tc, hum="vapor", label=f"{y}|{tc}")
            R[f"{y}_{tc}"] = r
            print(f"{y:10s} {tc:14s} {r['beta_pressure']:+11.2f} (z={r['z_pressure']:+6.2f})"
                  f"   {r['beta_hum']:+13.2f} (z={r['z_hum']:+6.2f})")
        print()

    print("== R2: humidity measured as RELATIVE humidity (grip 'feel') instead of vapour density ==")
    for y in ("break_mag", "spin"):
        r = fit(cells, games, m, y, temp_ctrl="bins", hum="rh", label=f"{y}|rh|bins")
        R[f"{y}_rh_bins"] = r
        print(f"  {y:10s} beta_RH={r['beta_hum']:+9.4f} per %RH (z={r['z_hum']:+6.2f})"
              f"   pressure {r['beta_pressure']:+8.2f} (z={r['z_pressure']:+6.2f})")

    print("\n== R3: equal-and-opposite test under nonparametric temperature control ==")
    r = R["break_mag_bins"]
    print(f"  break: pressure {r['beta_pressure']:+.2f}  vapour {r['beta_hum']:+.2f}  "
          f"excess {r['beta_hum'] + r['beta_pressure']:+.2f}  "
          f"equal&opposite z={r['z_equal_and_opposite']:+.2f}")

    json.dump(R, open(os.path.join(OUT, "robustness.json"), "w"), indent=2, default=str)
    print(f"\nWROTE {os.path.join(OUT, 'robustness.json')}")


if __name__ == "__main__":
    main()
