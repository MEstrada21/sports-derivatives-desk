# VARIANT LEDGER — corn sweat (task #50/#51)

**Why this exists:** parent prereg §5 requires that "the ledger records every variant," and
`analyze.py` references it, but **it was never produced.** The methods audit flagged that as a
prereg-compliance gap. This is the retrospective accounting, written 2026-08-09 under Amendment 3.

**Honest caveat on a retrospective count:** reconstructed from committed code and artifacts after
the fact. It is complete to the best of my reconstruction, but a ledger written *as you go* is
strictly better evidence than one written afterwards, and this one should be read as the weaker
form.

## Pre-named PRIMARY endpoints (the multiplicity that matters)

| # | stage | endpoint | pre-registered in | outcome |
|---|---|---|---|---|
| 1 | 1A | break magnitude vs air density | parent prereg | PASS (pressure channel clean) |
| 2 | 1B | HR/BIP vs dew point | parent prereg | UNDER-POWERED |
| 3 | 2 | corn-belt Jul–Aug dew anomaly | parent prereg | **CORN-UNRESOLVED** (restated A3) |
| 4 | A2 | equal-and-opposite on carry distance | Amendment 2 | **PREDICTION FAILED (rejects)** |

**Four pre-named primaries across the whole program.** Bonferroni at α=0.05 → 0.0125; the surviving
positive results (pressure channel z≈+14, carry pressure z=−7.8) clear that by orders of magnitude.

## Stage-1B family (the max-stat correction applies HERE and only here)

Six endpoints: HR/BIP (primary), vapour-density channel, K/PA, BB/PA, early innings, late innings.
Max-stat permutation n=400, family-wise critical |z| = 2.479. Only K/PA survives (|z|=3.55,
p_FW<0.0025). **Scope note (methods audit): the family-wise claim covers the Stage-1B family only —
it does NOT extend across Stage 1A, Stage 2 or Amendment 2.** Two defects disclosed: the
permutation draws were shared across endpoints rather than drawn independently per endpoint
(immaterial to the conclusion but incorrect), and the permutation null is slightly mis-centred
(mean z ≈ −0.2, sd ≈ 0.93 rather than 0/1).

## Every specification variant run

| group | variants | notes |
|---|---|---|
| Stage-1A specs | 2 | **spec v1 KILLED by its own permutation control** (no month FE); spec v2 adopted; Amendment 3 adds the tightened spec (hour FE + park×season FE) |
| Stage-1A endpoints | 7 | break, spin, velo, axis sin, axis cos, axis consistency R, break-per-1000rpm |
| Stage-1A subsamples | 4 | open-air, roofed, fixed dome, retractable |
| Stage-1A pitch families | 3 | fastball / breaking / offspeed (Amendment 3) |
| temperature-control specs | 2 | quadratic vs nonparametric 1 °C bins (both stages) |
| humidity parameterisation | 2 | vapour density deficit vs relative humidity |
| Stage-2 statistics | 2 | level contrast (parent, **artifact**) vs within-park shape DiD (correct) |
| Stage-2 park sets | 2 | all latitude-matched vs ex-Sutter Health |
| Stage-2 clustering | 2 | park bootstrap (**overstated**) vs season clustering (correct) |
| Amendment-1 DiD endpoints | 5 | break, spin, velo, HR, K |
| Amendment-2 carry | 1 primary + 4 controls | + nonparametric temp bins, roofed, EV placebo, LA placebo |
| K-thread era cuts | 4 | per-season 2023/2024/2025/2026 (rule-#7 correction) |

## Control runs (not variants — these can only fail, never flatter)

Permutation nulls: 300 (Stage 1B) + 400 (max-stat) + 60 (carry) + 300 (corn-label) + 60 (carry
corn-label) + 5 (A1 weather). Planted doses: 4 (Stage 1B) + 2 (Stage 1A) + 2 (carry) + 3 (upstream,
Amendment 3). Placebos: roofed, release velocity, release spin, launch speed, launch angle, BB/PA.

## Where the multiplicity risk actually sits

Not in the primaries — those were pre-named and the surviving ones clear Bonferroni easily. It sits
in **(a) the Stage-1B family**, which is corrected by max-stat, and **(b) the Stage-2 park-level
narrative**, where I read a per-park ranking off a statistic that was not the pre-registered one.
That second failure produced a wrong published conclusion ("Missouri/Illinois not
Minnesota/Michigan") and is retracted in Amendment 3.
