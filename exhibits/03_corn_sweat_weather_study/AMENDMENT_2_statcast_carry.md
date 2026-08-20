# AMENDMENT 2 — Statcast continuous carry endpoint + ball-as-hygrometer

**Date:** 2026-08-09. **Parent prereg:** `PREREG_CORN_SWEAT.md` sha256 `a6da2b71…` (NOT edited).
**Prior amendment:** `AMENDMENT_1_measurement_gap.md` sha256 `fb43b481…`.
**Authorisation:** operator approval relayed via team-lead — verbatim *"you have my approval for
anything Statcast related."* Scope: install `pybaseball` (or equivalent) and pull Statcast
batted-ball data.

## PROVENANCE — this one IS clean pre-registration, and here is exactly why

Unlike Amendment 1, nothing here is retro-fitted:

- The **data ask was registered in the parent prereg §6, in writing, BEFORE any results existed**,
  precisely so it could not be rationalised by a disappointing outcome. It reads: *"Statcast
  batted-ball data (exit velocity / launch angle / hit distance) turns this into a continuous
  endpoint and buys roughly the missing order of magnitude of power."*
- The **ball-as-hygrometer design was specified in Amendment 1 §A2** and hashed on 2026-08-09,
  while the data was confirmed absent from disk — i.e. before it could possibly have been peeked at.
- **This file is written and hashed BEFORE the pull runs and before any fit.** The endpoint
  definition, sample filters, sign predictions and controls below are all committed in advance.

So numbers produced under Amendment 2 carry **genuine pre-registration**, unlike Amendment 1's
exploratory status. That distinction is the point of keeping them as separate documents.

## Why this is worth the pull (the power argument, stated before the data arrives)

The parent study's binding constraint was that our only carry-sensitive outcome was a **binary** HR
flag: Stage 1B landed at z = +0.53 with a CI containing both zero and the physics prediction.
Stage 1A demonstrated the fix — swapping a binary outcome for a continuous physical readout (pitch
break) took the same underlying question from unanswerable to z = 13.

**Carry distance is the right continuous readout for the operator's actual claim.** Break measures
air density via the *pitched* ball; distance measures it via the *batted* ball, which is the
mechanism in question.

**Pre-registered power expectation.** ~443k batted balls, of which perhaps 18% fall in the
carry-relevant launch window (~80k, ≈9 per game); residual distance SD given launch conditions ≈
25–30 ft; vapour-channel residual SD 0.00172 kg/m³ (measured, parent study). Then
`SE(β_vapour) ≈ 27/√9 / (0.00172·√8686) ≈ 56 ft per kg/m³` against a physics slope of roughly
215 ft per kg/m³ (2.5 ft of carry per 1% density on a 400-ft fly) → **expected z ≈ 4.** Better than
HR's z ≈ 0.5, weaker than break's z ≈ 13, because there are ~9 useful batted balls per game against
~300 pitches. **If the realised power is materially worse than this, that is reported, not buried.**

---

## The endpoint

**PRIMARY (H2-1):** `hit_distance_sc` regressed on the two behaviourally-inert density channels,
with launch conditions absorbed **fully nonparametrically**:

```
distance ~ rho_dry + vapor_deficit
         + [EV bin x LA bin] fixed effects          <- nonparametric in launch conditions
         + temp + temp^2
         + wind_speed x (sin, cos of wind direction) x park     <- park-specific wind response
         + park FE + season x month FE
SEs clustered by game.
```

Launch conditions enter as **cell fixed effects on a 3 mph × 3 degree grid** rather than a smoother,
so no functional form is imposed. Conditioning on EV and LA is the correct identification: it asks
*given that the ball left the bat exactly like this, how far did it fly* — which isolates flight
aerodynamics from everything about the hitter, the pitcher and the pitch.

**Wind is the classic confounder for carry and gets real treatment.** We have speed and direction
but not park orientation, so direction is entered as sin/cos interacted with park, letting each park
estimate its own "blowing out to centre" response from the data instead of assuming one.

### Sample filters (committed now)

- batted balls with non-null `launch_speed`, `launch_angle`, `hit_distance_sc`
- **launch angle 10–50°** (airborne and carry-relevant; ground balls carry no aerodynamic signal)
- exit velocity ≥ 60 mph; distance > 50 ft
- regular season only (`game_type == 'R'`), 2023-03-20 → 2026-07-02 to match the parent corpus
- Coors excluded from the primary; roofed parks are the placebo set, not the primary

## THE DISCRIMINATING PREDICTION (this is the whole point)

On **pitch break**, the vapour channel was **3.3× too large** for aerodynamics, and the excess
traced to grip — humidity cuts release spin (z = −10.2) while barometric pressure does not
(z = −1.7).

**A struck ball has no grip channel.** Once EV and LA are conditioned on, nothing the pitcher's hand
did can affect how far the ball flies. Therefore:

> **PREDICTION: on carry distance, the equal-and-opposite test should PASS —
> `β_vapour ≈ −β_pressure` — where on break it FAILED at z = −8.2.**

This is a genuine risky prediction with a clear failure mode:
- **PASS** → the density mechanism is confirmed on the batted ball, the parent study's grip
  interpretation of the break excess is corroborated, and the operator's physics is vindicated at
  the mechanism level (while remaining far too small to trade).
- **FAIL with vapour still oversized** → the grip interpretation is wrong and something else is
  going on with humidity; the parent study's mechanism story needs revision.
- **FAIL with both channels ≈ 0** → carry is not measurably density-sensitive at our power, and
  Stage 1B's null is not merely a binary-outcome problem.

**Pre-registered magnitude:** ≈ 2.5 ft of carry per 1% of air density (Nathan), i.e. **roughly
215 ft per kg/m³**, on both channels.

## Secondary endpoints (pre-named, all subordinate to the primary)

1. **H2-2 Stage-1B upgrade.** Convert the measured carry coefficient into an implied HR effect and
   compare it to the parent Stage-1B estimate (+0.0053 pp/°C) and the physics prediction (+0.008).
   This is the "does the continuous endpoint resolve what the binary one could not" test.
2. **H2-3 ball-as-hygrometer / measurement gap, re-run on the right instrument.** The Amendment-1
   corn × Jul 10–Aug 31 DiD, now on carry residual. **Inference by corn-label permutation, never
   game-clustered SEs** — the treatment varies across only 7 open-air parks (Amendment 1's
   self-caught error; memory `park-level-treatment-needs-label-permutation`).
   Prediction under the operator's theory: **positive** carry residual in that cell.
4. **H2-4 Coors as a calibration check.** Coors sits ~15% below sea-level density. Its carry
   coefficient should agree with the within-park weather-driven slope. Reported, not used to fit.

## Controls (binding, same standard as the parent)

1. **Planted-signal positive control at two doses through the exact headline function**, one at the
   physics prediction (215 ft per kg/m³) and one at 5×; report recovery ratio and dose.
2. **Permutation null** — weather shuffled within park × month; must centre on zero.
3. **Roofed placebo** — valid for the **vapour** channel only. Carried forward from the parent
   study: **a stadium is not a pressure vessel**, so the barometric channel is expected to survive a
   closed roof and its survival is NOT evidence of confounding
   (memory `roof-placebo-is-not-a-pressure-vessel`).
4. **EV/LA placebo.** Exit velocity and launch angle are set at contact, before flight. Air density
   cannot affect them. Regressing **EV** and **LA** on the density channels must return ≈ 0; a hit
   there means selection or measurement drift, not aerodynamics.

## Multiplicity

**One** pre-named primary (H2-1, the equal-and-opposite test on carry). Three pre-named secondaries.
Anything else is exploratory and gets max-statistic permutation with the variant count reported.
No threshold scanning in the primary.

## Data provenance to be recorded on completion (per instruction)

Exact pull window, `pybaseball` version, Baseball Savant query dates, row counts before/after each
filter, and the cache manifest — written into `out/statcast_manifest.json` and summarised in
RESULTS.md. Pull is **idempotent** (per-day parquet, skip-if-present), **rate-limited**, and cached
inside this lane only.

## Leak status (unchanged, restated)

Statcast is **post-game** data, as is the ERA5 weather. Correct for a descriptive physics study;
**not available at decision time.** Nothing here may be carried into a live model without a
forecast-based redesign.

## Coordination

`baseball-consultant` and `quant-methods-auditor` are auditing v1 in background. **If their findings
require respecification, this amendment is superseded rather than silently edited**, and any change
is dated with a provenance line (`prereg-provenance-rules`).

---
*Frozen 2026-08-09 BEFORE the Statcast pull was executed and before any fit.*
