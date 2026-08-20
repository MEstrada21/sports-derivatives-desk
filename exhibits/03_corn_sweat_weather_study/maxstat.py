"""Max-statistic permutation for the Stage-1B exploratory family.

Six non-primary endpoints were scanned (vapour channel, K/PA, BB/PA, early, late, roofed). The
K/PA endpoint came back at |z|~3.6. An order statistic over six correlated tests is inflated, so
the honest reference is the distribution of the MAXIMUM |z| across the whole family under the
permutation null -- not the marginal z of the winner.
"""
from __future__ import annotations
import json, os
import numpy as np

from analyze import SEED, OUT, load, stage1b

FAMILY = [("vapour", "hr", "bip", "vapor_density_deficit"),
          ("K/PA", "k", "pa", "dew_point_c"),
          ("BB/PA", "bb", "pa", "dew_point_c"),
          ("early", "hr_early", "bip_early", "dew_point_c"),
          ("late", "hr_late", "bip_late", "dew_point_c"),
          ("HR (primary)", "hr", "bip", "dew_point_c")]
N_PERM = 400


def zs(games, mask, rng=None):
    out = {}
    for nm, yn, yd, key in FAMILY:
        r = stage1b(games, mask, y_num=yn, y_den=yd, key=key, rng=rng)
        out[nm] = r["beta_pp"] / r["se_pp"] if r["se_pp"] > 0 else 0.0
    return out


def main():
    games, _ = load()
    m = ((~games.is_roofed) & (~games.is_coors)).values
    obs = zs(games, m)
    print("observed |z| by endpoint:")
    for k, v in obs.items():
        print(f"  {k:14s} z={v:+7.3f}")

    maxes, per_ep = [], {k: [] for k in obs}
    for i in range(N_PERM):
        z = zs(games, m, rng=np.random.default_rng(SEED + 1000 + i))
        maxes.append(max(abs(v) for v in z.values()))
        for k, v in z.items():
            per_ep[k].append(v)
        if (i + 1) % 100 == 0:
            print(f"  ..perm {i+1}/{N_PERM}", flush=True)

    maxes = np.array(maxes)
    R = {"n_perm": N_PERM, "family_size": len(FAMILY), "observed_z": obs,
         "maxstat_crit_95": float(np.percentile(maxes, 95)),
         "maxstat_mean": float(np.mean(maxes)), "endpoints": {}}
    print(f"\nmax|z| permutation null: mean={np.mean(maxes):.3f}  "
          f"95th pct (family-wise critical value) = {np.percentile(maxes,95):.3f}")
    for k, v in obs.items():
        p_fw = float(np.mean(maxes >= abs(v)))
        p_marg = float(np.mean(np.abs(per_ep[k]) >= abs(v)))
        R["endpoints"][k] = {"z": v, "p_marginal_perm": p_marg, "p_familywise_maxstat": p_fw,
                            "perm_mean_z": float(np.mean(per_ep[k])),
                            "perm_sd_z": float(np.std(per_ep[k]))}
        print(f"  {k:14s} z={v:+7.3f}  perm-null z: mean={np.mean(per_ep[k]):+.3f} "
              f"sd={np.std(per_ep[k]):.3f}   p_marginal={p_marg:.4f}   "
              f"p_FAMILYWISE={p_fw:.4f}  {'SURVIVES' if p_fw < 0.05 else 'does NOT survive'}")

    json.dump(R, open(os.path.join(OUT, "maxstat.json"), "w"), indent=2)
    print(f"\nWROTE {os.path.join(OUT, 'maxstat.json')}")


if __name__ == "__main__":
    main()
