# Exhibit 07 — Instrument-Catch Vignettes

*Twelve bugs in our own measurement system, each caught before it moved a real-money decision.*

## Why a betting desk keeps a bug bestiary of its own instruments

The failure mode that kills quantitative systems is rarely a wrong model. A wrong model loses slowly and visibly — calibration drifts, grades sour, someone notices. A wrong **instrument** loses invisibly: every downstream number inherits the defect with full confidence attached, and the desk optimizes, sizes, and eventually bets against a ruler that was never straight. Worse, instrument bugs face selection pressure in the flattering direction — a defect that manufactures edge gets celebrated and shipped; a defect that hides edge gets investigated. So the audit burden cannot be a mood. It has to be structural: planted controls, independent re-derivations, reconciliations against sources that cannot share the bug, and an operator whose raised eyebrow is treated as a commissioning document rather than a complaint.

This desk keeps a numbered internal lineage of instrument catches — it runs past fifteen entries as of August 2026. The twelve below are the ones that can be told from public-data lanes (MLB StatsAPI, Kalshi's public API, the engine's own artifacts); a few others live inside vendor-licensed line data and stay out of a public document. Every one of these was caught **before** it moved a real-money decision. Several were caught while everything *looked fine* — which is the whole point.

**The planted-control philosophy.** A control that cannot fail is asserted, not verified. Before any null verdict banks, a known signal is planted and pushed **through the exact harness** that produced the null — if the harness can't see a signal we put there ourselves, its nulls are void. Before any positive verdict banks, the positive control must exercise the **exact function** the headline number calls — a green battery wired around a *different* code path is worse than no battery, because it converts an untested claim into a certified one. Controls report dose and magnitude, not just pass/fail. And when a control is green but a number is surprising, the number gets re-derived from raw artifacts by a second independent path before anyone believes it. Vignettes 2, 4, and 5 are what this doctrine looks like when it earns its keep; vignettes 6, 11, and 12 are what happens in the gaps between applications of it.

Format per vignette: **Symptom** (what looked wrong — or, worse, looked fine) / **The catch** (what noticed) / **Root cause** / **Blast radius** (what it would have cost undetected) / **Standing rule** (what it produced).

---

### 1. The phantom under-prediction (2026-06)

**Symptom:** the engine appeared to under-price full-game totals by roughly a fifth of a run per game; a root-cause work order was opened against the home-run tail.
**The catch:** the out-of-sample gate on the proposed fix — remapping reached-on-error to a single — *flipped* the model to significant over-prediction, which made no sense unless the baseline diagnosis was wrong. A source-check of the production pricing path confirmed it.
**Root cause:** the diagnostic priced totals on a regulation-9-innings path but graded against extras-inclusive realized totals. Production already priced with extras. The instrument manufactured the exact bias it reported.
**Blast radius:** a merged "fix" would have installed a real phantom-over tilt — systematically losing over bets — to cure a disease the engine never had.
**Standing rule:** totals calibration must price through the production extras path; never diagnose a model through a harness that doesn't share its settlement basis.

### 2. The false-null machine (2026-07)

**Symptom:** nothing. The sub-PA research program returned clean nulls — every arm, every model family, for weeks. Nulls are easy to believe.
**The catch:** a deliberately planted within-PA *leak* arm — a power control that should have blown the doors off — also read null. A control designed to be capable of failing, failing to fail.
**Root cause:** the research lane's private AUC helper had a rank-indexing bug that returned ~0.5 regardless of input. Perfect separation scored as a coin flip.
**Blast radius:** every grain-level null the program had ever banked was void; a live research thesis was nearly buried by its own ruler. With the fixed statistic, 9 of 9 arms cleared their confidence intervals at the single-inning grain (an existence result, not an edge claim — the distinction is policed as hard as the bug was).
**Standing rule:** no null verdict banks without a planted-signal positive control run through the exact harness. A null is only as good as its instrument.

### 3. The frozen-seed phantom (2026-07)

**Symptom:** the GPU port of the engine showed a small uniform offset versus the CPU oracle at overwhelming statistical significance (t in the hundreds at population scale). The port was quarantined as defective.
**The catch:** a falsification triad whose keystone was a **same-engine null** — the oracle compared against *itself* under two frozen base seeds reproduced the full "defect" signature with zero engine difference.
**Root cause:** frozen seed schedules pinned Monte-Carlo noise per cell across all games in both backends, and the z-battery assumed ~22,000 reads were independent when they shared ~18 frozen noise streams — compounding frozen noise into phantom systematic bias.
**Blast radius:** a healthy engine delivering a ~40× throughput gain would have stayed quarantined indefinitely — and the same harness pattern would have silently poisoned every future A/B comparison it touched.
**Standing rule:** every differential harness runs an engine-vs-itself null before its verdicts bank; seed schedules are unit-dependent; test statistics cluster on the actual correlation structure.

### 4. The swapped payoff branch (2026-07)

**Symptom:** a backtest lane printed a meaningful positive net taker edge on an exchange market — the kind of number that ends a validation program early.
**The catch:** an adversarial re-derivation of the ROI from raw records by a second, independent path — run *after* the lane's control battery had already blessed the number.
**Root cause:** the P&L helper's NO-side branch swapped the win and loss magnitudes (the docstring was right; the code was wrong) and its fee helper skipped the exchange's cent-rounding — jointly understating losses. The planted positive control had been wired through a *different* P&L function than the headline used, so a green battery certified code the read never called.
**Blast radius:** a phantom edge roughly an order of magnitude above the corrected value (which was ≈ flat), sitting one burst of enthusiasm away from a real-money conversation.
**Standing rule:** every positive control exercises the exact function the headline calls; surprising numbers are re-derived from raw artifacts by an independent path before banking.

### 5. The un-takeable baseline (2026-07)

**Symptom:** the first CI-clearing "beats the closing market" result in project history — the engine, with zero prop-specific tuning, appeared to out-price the close on a prop market, robust to three clustering choices *and* a multiplicity correction.
**The catch:** an internal reviewer challenge escalated to a three-lane adjudication — a symbolic derivation with pre-registered grid predictions, then an empirical grid — all three reproducing the artifact mechanism.
**Root cause:** proportional devigging inflates longshot probabilities (the favorite-longshot artifact), and thin one-book alternate rungs go stale — the yardstick was a price nobody could actually take. Under proper devig methods and a multi-book two-sided consensus filter, the "edge" collapsed to negative.
**Blast radius:** a false "we beat the close" credential would have anchored the program's forward plan — and its self-image — on an artifact. The calibration pass stood; the sharpness claim was retracted the same day it was minted.
**Standing rule:** any skill-vs-market claim must split main/alternate rungs and book depth before belief, and the baseline must be a takeable price. The grader may never be softer than the market.

### 6. Rows are not ticks (2026-08)

**Symptom:** nothing. The exchange collector's dedup logic tested green; every stored row was an honest, receipt-stamped observation; append-only law intact.
**The catch:** while smoke-testing a new sport's lane, the modal time gap between "duplicate" quote rows was exactly 15–16 minutes — precisely the collector's process-restart cadence. The signature pinned the mechanism.
**Root cause:** dedup keys were built with the language's built-in string hash, which is randomized per process. Every fresh collector process re-wrote every currently listed quote as "new."
**Blast radius:** quote-*movement* counts inflated 1.6–3.4× across process boundaries at the slate tier — any study counting rows as ticks (movement frequency, update intensity, staleness) was biased before it began. Not data corruption; a pure measurement hazard, which is the more dangerous kind.
**Standing rule:** dedup keys use stable content digests, never process-local hashes; analyses over the store dedup on content against the prior row rather than trusting row identity. Rows ≠ ticks.

### 7. The wrong-signed overlay (2026-08)

**Symptom:** an operator's felt anomaly — persistent, too-harsh grades on one team's away lines. "Is the engine misdiagnosing this team?"
**The catch:** an operator-commissioned four-lane audit with adversarial synthesis; both decisive lanes independently reproduced. The eyebrow was the instrument.
**Root cause:** the engine compresses favorites toward 50%. For *home* favorites, the flat home-advantage overlay accidentally cancels the compression — the graded number looks calibrated. For *away* favorites the same overlay **adds** to it, re-introducing several points of bias. A configuration defect hiding inside an accidentally-calibrated sibling; the team itself was innocent (mid-pack, inside league noise).
**Blast radius:** roughly 4 points of bias on every away-favorite grade — a week of declines graded too harshly. And a sequel: when the two-reading discipline later lapsed out of session memory for a week of nightly cards, six EV sign flips rode raw-only grades until the convention was moved into code.
**Standing rule:** cards print raw and overlay-adjusted readings side by side, enforced by the card renderer rather than habit; extreme-favorite reads carry an unreliable-zone flag; never patch a team to fix a configuration.

### 8. Means clean, shape broken (2026-08)

**Symptom:** none from the acceptance battery — the advancement-model re-fit preserved run means, passed, and ran in production.
**The catch:** the operator again, one day after vignette 7 — "check the engine at loaded bases against run expectancy." Measured, then adversarially verified, both independently reproduced.
**Root cause:** the re-fit preserved run **means** but broke the conditional run-distribution **shape** from runner-on-third states: the engine stranded both runners at half the empirical rate, over-produced exactly-one-run innings, and under-produced crooked innings. The kill-switch default model had the shape right all along.
**Blast radius:** every live jam-state read ran ~6–8 points too bearish on "at least one run scores" — escape prices, live unders, blowout tails, all graded through the defect for weeks.
**Standing rule:** acceptance batteries for distribution-generating changes must anchor **shape** (per-state strand rates), not just means. The mean is a misleading summary for anything priced off a tail — a lesson this project has now paid for twice.

### 9. The miracle cell and the leaky join (2026-08)

**Symptom:** two at once in a single commissioned study: a base-state reconstruction that read plausibly, and one cell of an 18-cell scan showing a strong positive with a naive p-value near 0.0001.
**The catch:** (a) validating the reconstruction against the tape's *own* independently recorded state — score agreed 98.7% of the time while outs agreed only 58.2%, and that asymmetry *is* the diagnosis; (b) a max-statistic permutation test the desk substituted for the commission's "CI-clear in any cell" spec, which as written carried a ~60% familywise false-positive rate.
**Root cause:** (a) a naive "last completed play before time t" join carries the previous half-inning's terminal state — three outs, stranded runners — across the inning boundary; (b) the miracle cell had n = 2.
**Blast radius:** run exactly as commissioned, the study banks a phantom tradeable cell and mislabels a third of its jam states. Instead it banked an honest kill.
**Standing rule:** play-by-play joins are scoped to (inning, half) and validated against the tape's own recorded state; every per-cell scan carries a max-stat permutation; power-check the cell grain before promising cell-level verdicts.

### 10. The phantom cent (2026-08)

**Symptom:** an exit fee on a tiny tennis position disagreed with the hand-computed value by exactly one cent.
**The catch:** the desk's habit of reconciling even trivial fills against the exact fee formula — a one-cent check on a throwaway-sized position ended up auditing the production grading stack.
**Root cause:** ceiling-rounding applied to a *float* product. Exact whole-cent products carried IEEE dust and rounded up an extra cent. Rounding up is correct exchange behavior; rounding up float noise is not — and the mismatches cluster exactly at round lots and round prices, i.e. the fills a desk actually places.
**Blast radius:** small in magnitude (fractions of a point of stake, no decision flipped) but systematic, all in one direction: overstated fees, understated edge. The desk first reasoned the direction *backwards* ("every no-go stands") before correcting itself: greens stand a fortiori; **boundary no-gos** are what an overstated fee can hide.
**Standing rule:** money arithmetic in exact decimal types with an explicit rounding mode, never float — and work a bias's directional implications out on paper, because a conservative bias is still a bias and its consequences are not symmetric.

### 11. The lying DONE marker (2026-08)

**Symptom:** everything looked fine for three consecutive nights — launch manifests recorded success, completion markers wrote clean.
**The catch:** an operator-commissioned audit ("make sure we don't have a bug laying around when we turn something on or off") that took **both** hypotheses seriously: it exonerated the engine — card rows reproduced to within a tenth of a point, calibration clean, the broken-engine statistical signature absent — *and* found the harness corpse next to it.
**Root cause:** a fee-fix commit added a top-level import that resolved in development sessions but crashed under the daemon's bare interpreter — every game launch died at import for three nights while success markers, written unconditionally, reported completion. A second drift rode along: a manually-swapped config pin had silently frozen days earlier.
**Blast radius:** three nights of paper receipts unrecoverable, and a record that lied in exactly the direction that prevents anyone from noticing. The commit that fixed one instrument bug planted the next.
**Standing rule:** bare-context import smoke tests for anything a daemon launches; completion markers exit-gated on verified child artifacts (with zombie-reaping before any process-liveness check); config that must track a daily artifact resolves dynamically with a loud log line — never by a manual swap that can lapse.

### 12. The guard that guarded the wrong key (2026-08)

**Symptom:** nothing. An idempotency guard existed, tested green, and the closing-line-value ledger accrued normally for a week.
**The catch:** settlement-night reconciliation that grouped the ledger by the preregistration's *own* definition of an observation — same contract at same price = one — and asserted every group had size 1. Nineteen groups didn't.
**Root cause:** the guard keyed on an entry id that embeds the seed timestamp — an **event** identity. Re-seeding the same quote later minted a fresh id and walked past the guard. Same defect family as vignette 6: the guard existed, tested green, and guarded the wrong key.
**Blast radius:** exact-copy duplicates barely move a mean — they fake the n and shrink the confidence interval. The quietest possible corruption of a significance test. (The habit continued paying: a later audit of the same instrument caught a printed confidence bound that failed independent re-derivation, and corrected it in place.)
**Standing rule:** dedup keys are built from exactly the fields of the prereg's observation definition, never from a convenience id; every accruing ledger gets a periodic group-by-and-assert-unique audit; a banked number must be re-derivable from disk.

---

## The pattern language

Three shapes recur. **The broken ruler** (1, 2, 3, 4, 10): the measuring code itself is wrong, and the fix is a control wired through the exact claim path. **The wrong identity** (6, 12): a guard or key that tracks something *adjacent* to the defined unit of observation, caught only by reconciling against the definition itself. **The silent lapse** (7, 11): a discipline that lived in habit or session memory instead of code, caught by audits that check the innocent explanation and the drift with equal seriousness. The through-line: none of these were found by staring harder at outputs. They were found by building things that could contradict us — planted signals, same-engine nulls, second derivations, reconciliations against independent state — and by treating "everything looks fine" as a claim requiring evidence, not a resting state.
