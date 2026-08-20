# Exhibit 06 — The K-Prop Failure

**A model that sat its exam, failed, was diagnosed to the mechanism, and did not ship.**

- **Market:** MLB pitcher-strikeout props (over/under a posted K line)
- **Verdict (banked 2026-07-16):** Gate-1 **MISCALIBRATED / NOT-SHARP** — not a Gate-2 candidate
- **Root cause:** not the strikeout model — the engine's **rigid 5-inning starter hook**
- **Production changes shipped:** **none**
- **What the failure spawned:** a calibrated starter-workload PMF, a live pull-hazard model (held-out AUC 0.945), and a standing desk rule about openers and thin cells

---

## 1. What was built, and why K-props looked attractive

The core engine is a plate-appearance-grain Monte Carlo simulator: a shrunk
Dirichlet-multinomial estimator feeds a per-PA outcome categorical, the engine
owns all base-out/advancement state, and every market is a read-off from
simulated paths. In July 2026 that engine had just passed a batter-prop Gate-1
calibration exam across seven markets (per-market ECE 0.003–0.026, statistically
tied with the devigged market close). Pitcher strikeouts were the obvious next
surface, for three reasons:

1. **The machinery already existed.** The production estimator computes the
   strikeout mass *before* collapsing outs into a single `out = K + in-play out`
   category. Building a FINE 7-category cell bank (K un-collapsed) required no
   new modeling — just declining to throw information away, with a walk-forward
   configuration matched to the production monthly banks.
2. **The composition was clean.** A validated per-PA P(K | out) read-off applied
   to the production 6-category path's OUT events, with K nested inside out, so
   the simulated paths were **byte-identical** to production. The locked control
   engine (standing rule: never restructured without out-of-sample evidence) was
   untouched.
3. **The per-event rate was demonstrably right.** Aggregate level bias was
   essentially zero: engine E[K] = 4.894 vs realized 4.867 per start.

A calibrated per-PA K rate composed over simulated innings *looks like* a
finished K-prop model. That resemblance is exactly what the exam existed to test.

## 2. The exam it sat — and how it failed

Every market in this program passes through the same two-gate discipline before
money is even discussable:

- **Gate 1 — Calibration:** do realized outcomes match the claimed probabilities?
  (Brier, ECE, reliability, stratified mechanism checks — needs only public
  outcome data.)
- **Gate 2 — Edge/CLV:** does the model beat real market closing prices? A model
  never reaches Gate 2 without passing Gate 1.

The exam was pre-registered (prereg on disk before grading), run in a research
lane with production code read-only, and graded against **realized strikeout
outcomes** — public data — across roughly 6,900 starter-games and ~550 starters,
Aug 2023 → Jul 2026 (lines sourced from a large licensed corpus, not
redistributable; no vendor price data is reproduced here). Controls all passed:
path-equivalence 3000/3000, FINE↔6-cat marginal consistency to ~1e-16 (the K
split did not distort the locked engine's marginal), a label-permutation leakage
check, and a planted-ε control that detects miscalibration when dosed.

**It failed — and failed with a specific shape:**

- **All-lines ECE 0.096; main-line ECE 0.146** — an order of magnitude worse
  than the batter markets (0.003–0.026) graded with the same instrument.
- **Level right, distribution wrong.** The mean was fine; the K distribution
  was far too **narrow**, so P(Over) quotes were systematically over-confident
  in both directions.
- **The realized-IP stratification was the mechanism proof.** Splitting graded
  starts by how long the pitcher actually lasted:

  | Realized-IP stratum | Engine mean P(Over) | Realized Over rate | Realized mean K | Read |
  |---|---|---|---|---|
  | **Short** (< 4.1 IP) | 0.517 | 0.259 | 3.15 | Massively **over-predicted** — engine credited innings never thrown |
  | **Hook-matched** (4.1–5.2 IP) | 0.465 | 0.427 (ECE **0.064**) | 4.65 | Where the 5-inning assumption ≈ holds, calibration is near batter-market quality |
  | **Long** (> 5.2 IP) | 0.418 | 0.544 | 5.85 | **Under-predicted** — engine capped the start at 5 innings |

  The aggregate level only *looked* fine because short-stratum over-prediction
  and long-stratum under-prediction cancel. That cancellation is precisely the
  kind of failure a level-only check would have blessed.
- It was also **not sharp**: Brier skill against the devigged market close was
  materially negative (−0.172, 95% CI [−0.189, −0.155], robust to game- and
  pitcher-clustering and to multiplicity correction). A label-permutation
  decomposition showed almost all of that deficit was the structural
  under-dispersion, not ranking information — the market and the engine ranked
  pitchers about equally well.

## 3. Root cause: the rigid hook

The production simulator gave **every starter exactly 5 innings** — a fixed
constant (`STARTER_LAST_INNING = 5`), i.e. exactly 15 recorded outs, near-zero
workload variance. But a real strikeout total is a **count prop composed over a
random workload**: K ≈ (per-PA K rate) × (batters faced), and batters faced is
dominated by how long the manager lets the start run. Delete the workload
variance and the K distribution collapses to too-narrow, no matter how good the
per-PA rate is. The hook-matched stratum calibrating to ECE 0.064 is the clean
in-data proof that the strikeout model itself was never the problem.

**Banked standing lesson:** for any count prop composed over a random workload —
pitcher K, pitching outs, batter PAs in shortened games — a fixed hook is a
first-order calibration limiter *even when the per-event rate is right*.

### The through-line: what the diagnosis spawned

The failure was specific enough to act on, and it seeded a family of work — all
of it research-lane, none of it wired into production pricing:

- **Starter-workload PMF (hook model, same window).** A walk-forward shrunk
  empirical predictive distribution over recorded outs (pitcher-own → tier →
  league, kernel-smoothed), composed over the validated per-PA K read-off. The
  workload PMF itself graded **calibrated** (PIT mean 0.503 / var 0.082 vs ideal
  0.500 / 0.0833; E[outs] 15.05 vs realized 15.05; ~93% of realized dispersion).
  Composing it **halved** pitcher-K ECE (0.097 → 0.053), moved the simulated
  K-SD from 1.81 → 2.28 (realized 2.47), and improved every IP stratum — with
  an anchor control (workload ≡ 15 outs) reproducing the banked failure numbers
  exactly, proving the workload was doing the work. Verdict: the marginal is now
  *honest*, but still **under-resolved** — a pregame empirical workload model
  cannot foresee short starts (short-IP stratum still ~0.49 predicted vs ~0.26
  realized), because it cannot see what the market sees: matchup, pitch-count
  plans, bullpen state, in-game blow-ups. Calibrated-but-not-sharp = still no
  Gate-2 candidacy. That negative was reported straight too.
- **Pull-hazard model (two days later).** If pregame workload resolution is the
  binding limit, the missing resolution must live in-game. A pre-registered
  L2-logistic discrete-time per-PA pull hazard (440,166 survival rows / 20,294
  starts, walk-forward train < 2026 → evaluate 2026) graded **AUC 0.945 / ECE
  0.006 held-out**, monotone in pitch count (hazard 0.005 below 40 pitches →
  0.319 at 90+). Split verdict: **pregame NULL** (confirms the closed pregame
  feature set), **live LARGE and CI-clear** — conditioning on realized in-game
  state collapses predicted-workload SD from 4.5 pregame to 1.92 by inning 5.
  The resolution K-props lack is real and recoverable, but only in-game — which
  converged with three other independent lanes on this program's live-accuracy
  thesis. Still Gate-1 only; no edge claim, no production wiring.
- **The opener rule (desk case law, filed 2026-08-15).** The same defect class
  resurfaced on the live desk: against an *opener* (a reliever making a start),
  the engine extends the listed starter's per-PA cell through a full starter
  window — the maximally wrong version of the rigid-hook assumption. Standing
  rule: when the starter-provenance screen flags an opener/role-mismatch or a
  thin cell, that game's engine numbers are demoted to **NO-VERDICT** and the
  desk grades against the market's devigged number instead. A one-off model
  failure became a permanent operating guardrail.

## 4. What shipped: nothing

- No pitcher-K pricing entered production. No paper portfolio, no forward
  collection commitment, no bet lane.
- The locked control engine was untouched (the exam's own consistency control
  proved the 7-category split left the production marginal bit-identical).
- The hook-model and pull-hazard code lives in the research lane
  (`research/props_k/`, `research/hook_model/`, `research/methods/pull_hazard/`),
  banked behind pre-registrations, awaiting the in-game data that could earn a
  next exam.
- What *did* ship is the standing rule — fixed workload = first-order
  calibration limiter for count props — and its desk-facing descendant, the
  opener rule. The banked conclusion stands verbatim: **the engine, as built,
  is not the instrument for K-prop tails.**

## 5. Why this exhibit exists

It would be easy to fill a showcase with the exams a model passed. This exhibit
is here because the failures are where the discipline is visible:

- The exam was **pre-registered before grading**, with planted controls that
  could catch a broken harness.
- The failure was **diagnosed to a mechanism**, not waved at — the stratification
  table above is the difference between "it's miscalibrated" and "it's the hook,
  the K rate is fine, and here is the stratum where the model is already good."
- The diagnosis was **acted on proportionately**: research follow-ups that
  graded honestly (one calibrated-but-not-sharp, one live-only), a standing
  rule, and zero production wiring.
- And the headline number the failure protected is the one that matters: a
  confidently narrow K distribution quoting 0.52 on Overs that hit 26% of the
  time is exactly the confident-but-wrong-near-the-money failure mode this
  program's gates exist to stop.

A pipeline that only reports wins is a marketing document. A pipeline that can
fail a model, name the mechanism, keep the salvageable parts, and ship nothing
is a measurement instrument. This exhibit is the instrument working.

---

*Provenance (private repo): the Gate-1 verdict, stratification, and controls are
banked in `reports/propsK_gate1_20260716.md` with prereg
`research/props_k/PREREG_propsK_gate1_20260716.md`; the workload-PMF results in
`reports/hook_model_gate1_20260716.md` (`research/hook_model/`); the pull-hazard
results in `research/methods/pull_hazard/` (2026-07-18); the opener rule in desk
memory (2026-08-15). All calibration statistics here are computed against public
realized outcomes (MLB Stats API); betting-line inputs came from a large
licensed corpus and are not redistributed.*
