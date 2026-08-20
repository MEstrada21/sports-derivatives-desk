# EXHIBIT 08 — k as in kappa: the shrinkage we tried to beat

Every number below is out-of-sample, on our own data, against our own model. The story is
simple: the production PA-outcome estimator contains a two-line conjugate formula, three
well-resourced campaigns were mounted to out-learn it, and the formula won all three.

*(Not to be confused with the other K on this desk: Exhibit 06 covers strikeout props, the K
market the engine itself flunked. Two failed Ks in one project — there, the model was the
miscalibrated party; here, the model's kappa is the thing nobody could beat.)*

---

## 1. The model

For each cell (a player/context slice) we observe a six-vector of PA-outcome counts
`n = (n_out, n_bb, n_1b, n_2b, n_3b, n_hr)`, `N = Σn`, and place a Dirichlet prior on the
cell's multinomial:

```
p ~ Dirichlet(κ·m)
```

where `m` is the prior-mean multinomial (the broader cell this one shrinks toward) and
`κ > 0` is the prior precision **expressed in pseudo-plate-appearances**. Conjugacy gives the
posterior mean — the shrunk point estimate the simulator consumes — in closed form:

```
p̂ᵢ = (nᵢ + κ·mᵢ) / (N + κ)
```

equivalently a convex combination with an explicit shrinkage weight:

```
p̂ = w·m + (1−w)·p_empirical,    w = κ / (N + κ)
```

Three design choices matter:

- **κ in pseudo-observations is the interpretable parameterization.** κ = 200 reads as "the
  prior is worth 200 PA; trust the cell's own data once it has materially more than that."
  N = 0 returns the prior exactly; N → ∞ returns the raw rate. A concentration parameter in
  the same units as the data is a number a human can sanity-check against roster reality
  (a September call-up has 40 PA; a full season is ~600).
- **w is stored per cell as an auditable field** (`FeatureRow.shrinkage_weight`, 0 = pure
  empirical, 1 = pure prior), so any downstream lane can see at a glance which cells are
  prior-dominated and must not drive signal.
- **The prior mean is hierarchical**: a cell's `m` is the posterior mean of its parent —
  base/out cell → batter-vs-pitcher → platoon → regime-only → a fixed, documented league
  root prior — standard empirical Bayes, borrowing strength from the broadest level with
  data.

Production constants: κ = 200 (estimator default), and in the two-stage regime split
κ_discipline = 200 pseudo-PA (walk/K/ball-in-play stage) and κ_contact = 150
pseudo-batted-balls (hit-mix stage).

That's the whole estimator. Empirical rates plus pseudo-counts. v1 shipped it with an
explicit label: "empirical rates + shrinkage, NOT ML."

---

## 2. The temptation

Look at any thin cell and the formula seems to be committing a crime. A hot call-up with
40 PA carries w = 200/240 ≈ 0.83 — five-sixths of his estimate is somebody else's prior. A
pitcher with a new pitch, a platoon cell with 25 PA, a batter whose underlying contact
quality changed — all crushed toward the parent. Surely a model that *learns* its pooling —
per-player, per-context, from data — beats a fixed κ = 200 that treats every cell alike.
Every modern-ML instinct says the fixed pseudo-count is the naive baseline you graduate
from.

That intuition was tested three times, each time with more firepower.

---

## 3. Round one (2026-06-26): the negative control does its job

The original bake-off priced every arm through the identical Monte-Carlo engine on a strict
temporal split (train < 2026-06-01, eval ≥; game-id overlap asserted 0; 297 games / 2,561
single-inning innings / 22,549 held-out PAs). Control parity was exact — the structural arm
reproduced the baseline single-inning AUC 0.5250 to four decimals, so every challenger
number sits on the same footing.

**Arm B — the no-shrink probe — was a labeled negative control, not a contender**: raw
per-player empirical rates from the train window, shrinkage deleted, everything else
identical. Out-of-sample per-arm AUC (report table):

| arm | single-inning | F3 | F5 | F7 | F9 |
|---|---:|---:|---:|---:|---:|
| A — control (Dirichlet shrink + log5) | **0.5250** | 0.6014 | 0.5914 | 0.5807 | 0.5732 |
| B — no-shrink probe | **0.5012** | 0.5511 | 0.5650 | 0.5474 | 0.5497 |
| C — XGBoost | 0.5167 | 0.5834 | 0.5883 | 0.5790 | 0.5768 |
| C — LightGBM | 0.5182 | 0.5881 | 0.5829 | 0.5843 | 0.5712 |
| D — ridge | 0.5165 | 0.5930 | 0.5980 | 0.5805 | 0.5627 |
| D — lasso | 0.5162 | 0.6041 | 0.6003 | 0.5833 | 0.5671 |

The overfit signature, spelled out: raw empirical rates are the maximum-likelihood fit of
the training window — zero bias on the data they were counted from, maximal variance
everywhere else. A 40-PA cell's raw rate is mostly sampling noise, and the probe carries
that noise into pricing at face value. In-sample it looks like player-specific signal;
out-of-sample the single-inning read collapses to 0.5012 — a coin flip — and the paired
bootstrap (1,000 resamples) calls it real: ΔAUC vs control −0.0238 [−0.0389, −0.0091], the
largest significant deficit in the table. (On the later powered per-PA screen the same probe costs
+0.142 nats/PA of log-loss, CI [+0.133, +0.151] — raw thin-cell rates aren't a bolder
estimate, they're a strictly worse one.)

The challengers fared little better: ridge −0.0084 [−0.0165, −0.0005] and lasso −0.0087
[−0.0169, −0.0009] significantly worse on single-inning; XGBoost −0.0084 [−0.0178, +0.0008]
and LightGBM −0.0068 noise; every First-N delta CI covering 0. On per-PA multiclass
log-loss the control was best outright (1.03446 vs ML 1.0355–1.0375, league-marginal floor
1.04066). Verdict: **KEEP everything, rebuild nothing** — shrinkage is essential, the grain
is right, the no-shrink probe proves it.

---

## 4. Round two: the rematch, properly armed

Round one had a legitimate hole, and the operator called it: the ML arms were fed the
control's **own pre-shrunk rate vectors** as features, so they could only ever learn a
function of the control's output — structurally capped at "tie the shrinkage." The rematch
(pre-registered, frozen before compute) fixed exactly that, in two acts.

**Act 1 — learn your own shrinkage (2026-07-08).** New arms worked from raw
`batter_id × pitcher_id` identity: **E1**, cross-fitted target encoding with the EB
smoothing constant *learned by the model* (it chose m = 400 pseudo-observations — note it
learned *more* shrinkage than production's κ = 200, not less), and **E2**, a GPU
entity-embedding net over raw IDs plus context. Evaluation was powered up to 3,734 games /
2 seasons / 281,736 held-out PAs on fresh production weekly banks, with game-clustered
bootstrap CIs.

The integrity gates are the point. Before any challenger was read, the harness had to pass
a **planted-oracle positive control** — the control's own probabilities blended 6% toward
the realized outcome (ε = 0.06), fed through the exact readout path. A harness that cannot
detect a *known* winner proves nothing when it reports a null; "no arm cleared" is only
evidence if the instrument demonstrably clears when a real edge exists. The plant was
detected everywhere: per-PA Δlog-loss −0.18156 [−0.18273, −0.18034], and money-grain ΔAUC
+0.155 (F3), +0.241 (F5), +0.312 (F7), +0.455 (FG), every CI clear. A same-engine A-vs-A
null covered zero on every market, and the achieved First-N ΔAUC MDE was 0.0132 — the
harness could see, and could not hallucinate.

It promptly earned its keep. On stale annual banks E1 appeared to clear F5 (+0.0136
[+0.0001, +0.0265]) and FG (+0.0130 [+0.0014, +0.0256]) — briefly, "ML wins." With fresh
production-strength weekly banks the clear collapsed: F5 −0.00022 [−0.01116, +0.01054],
FG −0.00181 [−0.01196, +0.00824]. Diagnosis: *more shrinkage wins when the control's cells
are artificially data-starved* — a stale-bank artifact, caught by the gates, not a
challenger victory. Final read: no arm cleared any market; E2's raw-ID embedding was
significantly **worse** per-PA (+0.00225 [+0.00067, +0.00378] nats on the original window)
despite verified training convergence — at ~150–200 PA per player, a learned representation
overfits the training regime, and explicit hierarchical shrinkage absorbs the train→eval
shift better.

**Act 2 — tune everything (2026-07-15).** Remaining critique: hand-set hyperparameters. So:
Optuna TPE, 50 trials per arm per fold, nested walk-forward CV (three leak-safe outer folds,
Apr/May/Jun 2026; inner selection strictly inside each training pool; pooled outer eval =
91,283 PAs / 1,205 games), GBDT arms handed the control's log-probs *as input features* —
the fairest possible framing. Its own planted oracle: ε = 0.06, Δ = −0.18325 [−0.18537,
−0.18103], detected. The tuning genuinely worked — every fold's tuned LightGBM beat the
hand-set config on the inner objective. And on the held-out outer folds every tuned arm was
still slightly, *significantly worse* than the control: LightGBM +0.00066 [+0.00019,
+0.00111], XGBoost +0.00098 [+0.00049, +0.00147], ridge +0.00068 [+0.00017, +0.00115]
nats/PA. Nothing cleared on the improving side, anywhere. (A later screen ran two more
challengers lifted from a published "beats the market" claim — SVM-RBF and QDA — through the
same gated harness; both killed, same shape.)

Verdict, now definitive: **KEEP the control.** The wall is the representation and the data,
not the estimator, and not the tuning.

---

## 5. Sidebar: fighting the prior from the other direction

One more way to bet against the shrinkage machinery: keep the engine, but shrink its *live
output* toward the market instead of trusting the hierarchy — a global affine map
`p* = m + λ̂(e − m)` fit walk-forward on collected in-game quotes (2,939 held-out quotes /
451 games). Result: p* does not beat the market (ΔBrier vs market −0.00127 [−0.00418,
+0.00147]); the in-sample λ̂ = +0.278 [−0.235, +0.801] straddles zero. That λ̂ map is the
provably-optimal single-market recalibration — there is no cleverer calibration left to
design on this information. Fighting the prior with a market anchor is just as dead as
fighting it with gradient boosting.

---

## 6. Operational epilogue: the bracket, not the raw rate

The desk still gets asked — regularly, in live operation — to "un-shrink" a thin cell: the
opener with 60 PA of exposure, the call-up on a heater, the veteran whose last three starts
"obviously" changed his profile. The standing answer is never to trust the raw rate,
because the no-shrink probe already priced raw rates: −0.024 AUC and +0.14 nats/PA. The raw
thin-cell number is not suppressed information; it is measured noise.

The standing answer is a **sensitivity bracket**: price the state three ways —

1. **production shrink** (κ as shipped; read `shrinkage_weight` to see how prior-dominated
   the cell is),
2. **less-shrunk variant** (lower κ, tilted toward the cell's own data),
3. **market devig** as the outside reading —

and let agreement carry the verdict. If the conclusion flips inside the bracket, the cell
has no verdict, and the standing thin-cell rule applies: anchor to the market, demote the
engine to NO-VERDICT for that game. The legitimate open frontier is not *less* shrinkage
but **better shrinkage targets** — covariate-shaped priors for thin cells (shrink a
call-up toward a scouting-shaped multinomial instead of the league parent), and the one
honest residual from Act 1: E1's learned-m gives a statistically real but micro per-PA
calibration gain (−0.00169 nats [−0.00196, −0.00143]) that never translated to any market's
discrimination — filed as a tuning question *inside* the control, not a rebuild.

---

## 7. The prior is load-bearing

Two armed campaigns — three counting the tuning pass — with GPUs, HPO, raw-identity
representations, learned shrinkage, planted-oracle-verified harnesses, and multi-season
powered evaluations, all lost to `p̂ᵢ = (nᵢ + κ·mᵢ)/(N + κ)` with κ = 200.

That is not a statement about gradient boosting. It is a statement about the information
budget: at ~150–200 PA per player-cell per season, most of what a flexible model can extract
from a cell is variance, and hierarchical pooling with a fixed, honest pseudo-count is
close to the optimal response. The shrinkage is not a regrettable approximation waiting for
enough ML to remove it — it *is* the model's knowledge of how little a thin cell knows.
Beating it requires new information (a different representation, or years more data), not a
better function of the same counts. Until then the reopen gate stays where the verdicts
left it: WATCH, don't build — and when a thin cell looks over-shrunk, bracket it.

---

## Sources (repo-relative; every number above verified against these)

| # | artifact | what it carries |
|---|---|---|
| 1 | `src/bbs/features/estimator.py` | model docstring: Dirichlet(κ·m), posterior mean, w = κ/(N+κ), hierarchy, `shrinkage_weight` field; κ default 200 |
| 2 | `src/bbs/features/regime_split.py` | κ_discipline = 200 pseudo-PA, κ_contact = 150 pseudo-BBE |
| 3 | `reports/estimator_bakeoff_final_20260626T185002Z.md` | round one: per-arm table, Arm-B collapse 0.5250→0.5012 (Δ −0.0238 [−0.0389, −0.0091]), challenger CIs, per-PA log-losses |
| 4 | `research/methods/estimator_bakeoff_v2/PREREGISTRATION.md` | rematch contract: Arm B "labeled negative control," Arm E "learn your own shrinkage / representation," freeze mechanics |
| 5 | `research/methods/estimator_bakeoff_v2_boxpull/out/` | Act-1 results: `reprice_fresh/perpa_fresh.json` (281,736 PA; B +0.1422; E1 −0.00169 CI-clear micro), `reprice_result.json` (stale-bank E1 clears F5/FG), `reprice_fresh/confirm_result.json` (fresh-bank collapse), `reprice_fresh/gate_planted.json` + `reprice_fresh/gate_ava.json` (planted oracle + A-vs-A gates), `challenger.json` (E2 worse, E1 learned m = 400) |
| 6 | `research/ml/hpo_bakeoff/` | Act-2: `PREREG.md` (nested CV), `out/HEADLINE.json` (pooled 91,283 PA; all tuned arms CI-clear worse), `out/run_full.log` (planted −0.18325, detected), fold metas (tuned beats hand-set inner) |
| 7 | project memory `estimator-bakeoff-fair-shot-keep.md` | definitive-close narrative incl. stale-bank artifact + SVM/QDA addendum |
| 8 | project memory `l1-shrink-toward-market-verdict.md` | L1 shrink-toward-market null (ΔBrier vs market −0.00127 [−0.00418, +0.00147]) |
