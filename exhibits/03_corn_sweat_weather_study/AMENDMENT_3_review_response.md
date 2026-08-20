# AMENDMENT 3 — response to the domain review and the methods audit

**Date:** 2026-08-09. **Parent prereg** `a6da2b71` (unedited). **A1** `fb43b481`. **A2** `f1be4880`.
**Provenance:** post-data corrections and new tests responding to two independent reviews
(`corn-review-domain`, `corn-review-methods`). **Everything here is EXPLORATORY / CORRECTIVE**, not
pre-registered — except where it re-runs a pre-registered statistic under a corrected specification,
which is noted per item. No frozen document was edited; corrections supersede.

---

## RETRACTIONS — things I banked that were wrong

### R1. Stage 2: `CORN-CONFIRMED` → **`CORN-UNRESOLVED`** *(reproduced, not accepted on trust)*

The clustering unit is the **season**, not the park. July–August Midwest dew point is **synoptic** —
all seven corn parks sit under one Gulf-moisture regime, so a summer is roughly **one effective
draw**, not seven. My park-cluster bootstrap treated 7 parks as 7 independent draws.

Per-season corn-minus-control (my reproduction): **2023 +0.069 °C, 2024 +0.071 °C, 2025 +2.901 °C.**
Season-clustered: mean +1.014, sd 1.635, n=3, **t-CI [−3.05, +5.08] — contains zero.**

It also fails on the *correct* statistic: season-clustered within-park **shape** DiD = +1.242 °C,
**CI [−3.25, +5.74]**, again driven almost entirely by 2025 (−0.03 / +0.44 / +3.31).

> **The corn signature is a ONE-SEASON result. Restated everywhere.**

*(My per-season values differ slightly from the reviewer's quoted +0.25/+0.03/+2.97 — band/park-set
definitions differ marginally. Same conclusion, and I report my own numbers.)*

**This is the same trap class as my own Amendment-1 catch, one level up.** I caught park-level
pseudo-replication in A1 and then committed season-level pseudo-replication in the parent. The
generalised rule is now banked: *identify the level at which the treatment actually varies, and
cluster there — for weather, that is usually the synoptic regime, i.e. the season.*

### R2. "Missouri/Illinois, not Minnesota/Michigan" — **RETRACTED as a spec artifact**

`analyze.py` `stage2()` fits a **global** dew model with **no park fixed effect**, so its per-park
residual is a **LEVEL contrast** (Midwest-interior vs Northeast-coastal climate) — *not* the
pre-registered **within-park SHAPE** statistic. Under the correct tassel-window-minus-shoulder DiD:

| park | level (parent, artifact) | rank | **SHAPE (correct)** | rank |
|---|---|---|---|---|
| **Target Field** | −0.46 | 11 | **+1.86** | **1** |
| Kauffman | +1.59 | 2 | +1.48 | 2 |
| Rate Field | +1.26 | 3 | +1.11 | 3 |
| Busch | +1.93 | 1 | +1.10 | 4 |
| Comerica | −0.56 | 12 | +0.75 | 7 |
| Wrigley | +0.72 | 5 | −0.92 | 13 |

**Target Field goes from rank 11 to rank 1.** Minneapolis simply has a cool baseline; the *shape* —
which is what corn transpiration would move — is the largest in the sample. Comerica stays weak on
both (agronomically right: Michigan is minor corn, Detroit is lake-moderated). The published park
narrative was wrong and is withdrawn.

### R3. Amendment 1 §A3 — UHI sentence **withdrawn**

I wrote that urban heat island explains Target Field and Comerica's negative dew anomalies. **That
is incorrect physics: UHI lowers *relative humidity* at constant *dew point*, so it cannot produce
a dew-point anomaly.** The RH-vs-dew teaching note itself stands and is unaffected. An internal
check independently kills urbanity as the explanation anyway: Busch, Great American, Rate Field and
Wrigley are all urban and all positive on the level contrast.

### R4. `MECHANISM-REDIRECTED (grip dominates)` — **REJECTED, and now positively disfavoured**

The methods audit rejected the grip label as over-claiming. **The spin-axis test I ran under this
amendment goes further: it makes grip the *disfavoured* candidate.** See below.

### R5. "Replicates out of sample" (K-thread) — **withdrawn as corroboration**

Split-half validation *after pooled selection* is ancillary — the likelihood ratio is exactly 1.00,
so it adds no evidence. It is retained only as a stability check. The finding's actual support is
the pooled family-wise z = 3.55.

### R6. Planted dose — **relabelled POWER CALIBRATION, not a positive control**

The plant entered *downstream of* `load()`, so for a linear estimator recovery at ratio 1.000 is an
**algebraic identity that cannot fail**. It tested nothing about the join, the filters or the
formulas — the `pnl_taker` lesson. A **real upstream control** now exists (below).

---

## NEW EVIDENCE

### N1. THE SPIN-AXIS TEST — the decisive experiment, and it disfavours grip

Both reviewers independently named this. Data was already on disk (`spin_axis_degrees`, ~100%
populated); no new pull. 1.74M pitches, tightened spec (first-pitch-hour FE + park×season FE).
Spin axis is circular, so it enters as its two linear components plus the resultant length
**R = release-axis consistency**.

| endpoint | vapour z | pressure z | reading |
|---|---|---|---|
| release spin rate | **−10.66** | −0.93 | release kinematics DO move |
| axis sin / cos | −2.04 / −1.24 | −0.96 / −0.09 | axis barely moves |
| **axis CONSISTENCY (R)** | **+0.83 (NULL)** | −1.32 | **release is NOT scattered** |
| break per 1000 rpm | **−4.25** | +11.78 | aerodynamic response per unit spin DOES change |
| release velocity | −1.36 | −0.41 | null |

**Grip predicts:** rate falls ✓, axis shifts (weak), **consistency degrades ✗ (null)**.
**Pure surface/aero predicts:** release untouched ✗ (rate clearly moves).
**Neither single story fits.**

**The pitch-type ordering is what turns grip from "unproven" to "disfavoured":**

| family | pitches | break excess ratio |
|---|---|---|
| fastball | 968,755 | **3.03** |
| offspeed | 230,539 | 2.93 |
| **breaking** | 534,915 | **1.68** |

Breaking balls demand the **most** finger friction to spin, so a grip mechanism predicts they suffer
**most**. They suffer **least** — the ordering is inverted. (Independently reproduced: the audit
reported 3.17 vs 1.69, I get 3.03 vs 1.68.)

> **Adopted wording: a NON-AERODYNAMIC humidity channel exists; its identity is UNRESOLVED. Grip is
> now positively disfavoured (axis-consistency null + inverted pitch-type ordering). The remaining
> candidates — ball surface/seam-wake and optical spin-measurement quality — are not separated by
> this test.** Progress here is *eliminating* a candidate, not confirming one.

The **pressure→spin z ≈ 0 result stands** as proof the channel is non-aerodynamic; it simply does
not name the channel.

### N2. Exact-proportionality — the strongest evidence the pressure channel is clean aerodynamics

Break is a Magnus quantity, so `break = k·ρ` implies the slope must equal `mean_break / mean_ρ`
exactly: **14.630 / 1.1754 = 12.45 in per kg/m³.** Fitted pressure channel: **14.06 ± 0.93**,
departure **z = +1.73 — indistinguishable from exact proportionality.** That is far stronger than
"the sign is right."

### N3. Rule #7 violation in the K-thread — corrected

True ABS debut is **2026-03-25**, and walk/K may never be pooled across it. My banked
"fit 2023-24 → held-out 2025-26" split put **pre-ABS 2025 and post-ABS 2026 in the same bucket.**
Per season:

| season | regime | β (pp/°C) | z | note |
|---|---|---|---|---|
| 2023 | pre-ABS | −0.0667 | −1.91 | |
| 2024 | pre-ABS | −0.0678 | −1.74 | |
| 2025 | pre-ABS | −0.1225 | **−3.43** | |
| 2026 | **post-ABS** | −0.0004 | −0.01 | **0 Jul–Aug games in corpus — uninformative BY CONSTRUCTION** |

All three pre-ABS seasons share the sign. 2026 cannot speak: it is both a different regime and
stops 2026-07-02, before the window the effect lives in.

**Magnitude honesty (domain review):** the implied elasticity (~2.5) is **2–5× larger than the
literature's 0.5–1.0** for the movement→whiff channel, so **movement accounts for perhaps a fifth
to a half of it**; the rest is unexplained.

**Under-sold support, now stated:** the **BB placebo is FLAT (z = −0.65)** against K at z = −3.55.
A movement/whiff channel predicts exactly that split; a *command* channel would move both. The flat
BB is a **discriminating null, not a boring one.**

### N4. A real UPSTREAM positive control

Planted at the **raw weather level**, upstream of every join, filter and weight:

| upstream dose | recovered net |
|---|---|
| 0.000 | +0.0000 |
| 0.020 | +0.0082 |
| 0.050 | +0.0217 |

Doses are one-sided (HR counts can only be added), so recovery is ~half the nominal dose by
construction. What matters is that a signal injected **before** the pipeline survives it — which the
post-`load()` plant never tested.

### N5. Amendment-1 measurement-gap null is INDEPENDENTLY STRENGTHENED (reviewer's constructive point)

My five weather-permutation draws sat at **z ≈ −2.0 to −2.3** while the real fit was **z = −1.23**.
That gap means the **measured weather is absorbing real corn-August signal** — the station data is
doing its job. It is positive evidence *for* the measurement-gap null, and I had recorded it only as
a diagnostic.

---

## Disclosures the audit required

- **Excess ratio restated 2.7–3.4×** (hour FE moves the pressure channel ~14%). In natural units
  over a p5–p95 humidity swing: **break −1.51%**, spin −0.53%, break-per-rpm −0.76%.
- **Support asymmetry disclosed:** the vapour and pressure channels do not carry equal statistical
  weight (~3.55:1), so "3× excess" is not a comparison of two equally-measured quantities.
- **Interpretive asymmetry disclosed:** I read a 1.3–1.6× density-vs-density gap (Coors vs pressure
  channel) as *corroboration* while reading a 2.7–3.3× gap as a *new mechanism*. Those are not
  obviously different in kind, and the Coors constants in `analyze.py` are **hard-coded** rather
  than regenerated from committed code (the auditor could not reproduce the 919-pair figure; the
  defensible slope range is 17.2–19.6). **Regenerating them is an open item.**
- **Absorbed-FE degrees of freedom** are not deducted, understating SEs by ~3.5% — immaterial to
  every verdict, disclosed.
- **`|ivb|`-vs-`hypot` spec drift** logged: Stage 1A uses total break magnitude `hypot(hb, ivb)`,
  which is not identical to the induced-vertical-break framing used in some diagnostics.
- **`pitch_type` is endogenous** — conditioning on it means within-type coefficients are **LOWER
  BOUNDS** (favourable to the finding's direction, but logged).
- **`s1a_spin_placebo` was all-NaN** in `results.json` (missing `dropna`); superseded by N1.
- **`cell_permutation` `spin_era` sign flip must NOT be read as replication** — it is a stability
  diagnostic on an already-null result.
- **Variant ledger** now exists (`VARIANT_LEDGER.md`) — a retrospective reconstruction, which is
  weaker evidence than a contemporaneous one, and labelled as such.

### N6. ROOF-STATE SPLIT — the clean placebo now exists, and it ESCALATES the doubt

`roof_state.parquet` (already on disk from the `leverB_parkwind` lane, sourced from StatsAPI
`gameData.weather.condition`) gives **actual per-game roof state** for all 7 retractable parks:
1,886 matched games, 1,282 closed / 604 open. **No new pull.** This converts the broken
pre-registered placebo — which pooled closed-roof games with roof-*open* games — into a clean one.

Predictions were stated before fitting: under a **closed** roof the vapour channel should go to
**zero** (climate-controlled air severs it) while the pressure channel should **survive** (a stadium
is not a pressure vessel).

| sample | pitches | pressure channel | vapour channel |
|---|---|---|---|
| open-air (reference) | 1,743,286 | +11.91 (z=+12.98) | −39.09 (z=−12.96) |
| retractable, roof OPEN | 171,833 | −5.43 (z=−1.19) | −53.41 (z=−3.88) |
| **retractable, roof CLOSED** | 361,627 | **+9.50 (z=+5.87)** | **−32.57 (z=−5.91)** |

- **Pressure: prediction CONFIRMED.** It survives a closed roof at +9.50 (z=+5.87), close to the
  open-air +11.91 — exactly what "a stadium is not a pressure vessel" requires. The physics rescue
  of that placebo is now empirically earned, not merely argued.
- **Vapour: prediction FAILED.** It survives a closed roof at **83% of its open-air magnitude**
  (−32.57 vs −39.09, z=−5.91). The ball is flying through **conditioned indoor air**, so outside
  humidity cannot be reaching it aerodynamically.

> **This escalates the doubt rather than resolving it.** A vapour coefficient that barely weakens
> indoors is not merely "non-aerodynamic" — it is consistent with a **residual seasonal/temporal
> confound that park + season-month fixed effects do not fully absorb.** "Residual confound" is now
> a live candidate *alongside* "real non-aerodynamic mechanism," and I cannot separate them here.
> The honest position weakens from *"a non-aerodynamic humidity channel exists"* to **"a
> humidity-correlated signal exists that is definitively not air density, and may not be a
> mechanism at all."**

**Discordant result, reported not buried:** at retractable parks with the roof **open**, the
pressure channel is −5.43 (z=−1.19) — wrong-signed and null, where open-air gives +11.91. Possible
causes (untested): roof-open games are a weather-selected sample that compresses the pressure range,
or n=171k is simply too small. Either way it does not fit cleanly and is flagged.

### N7. COORS CONSTANTS REGENERATED — the banked 19.3 is NOT reproducible

The auditor could not reproduce the hard-coded 919-pair figure. Regenerated from committed code
(`roof_and_coors.py`) across defensible filter choices:

| filter (min Coors / min other / min n) | pairs | break ratio | slope (in per kg/m³) |
|---|---|---|---|
| 2 / 10 / 3 | 878 | 77.4% | **18.0** |
| 2 / 10 / 1 | 1,136 | 77.9% | 17.4 |
| 5 / 20 / 3 | 144 | 77.8% | 17.3 |
| 10 / 50 / 3 | 20 | 80.3% | 15.9 |
| 1 / 5 / 3 | 1,979 | 77.9% | 17.4 |

**Regenerated range 15.9–18.0.** The banked constant **19.3 sits OUTSIDE that range** and the
919-pair count does not reproduce (878 at the same nominal filters) — it came from an uncommitted
inline snippet. **Replace the point estimate with the range everywhere.** The qualitative
conclusion is unchanged (Coors agrees with the pressure channel, not the vapour channel), and if
anything the agreement is *tighter* at 15.9–18.0 against a pressure channel of ~12–14.

### N8. Amendment 2's carry plants get the SAME relabel

The A2 carry plants (215 and 1075 ft per kg/m³, recovered at ratio 1.000) have the **identical
linear-identity property** as the Stage-1B plants — they enter downstream of the data build and
therefore cannot fail. **Relabelled POWER CALIBRATION, not positive controls**, everywhere.

## Open items NOT done here

- ~~Roof-state split~~ — **DONE, see N6.** The field was already on disk in `leverB_parkwind`;
  no pull was needed. Pressure rescue empirically earned; **vapour rescue FAILED.**
- ~~Coors constants~~ — **DONE, see N7.** Banked 19.3 replaced by the range 15.9–18.0.
- **USDA NASS + Drought Monitor + multi-year ERA5 weather-only design** — the real fix for n=3
  seasons is **more YEARS, not more games.** Awaiting operator sign-off; **not pulled.**
- **Statcast `hitData` re-parse** — authorized, but **found redundant**: Savant already covers
  8,499/8,686 = **97.9%** of the same games with the same fields. Its one distinct value is that
  StatsAPI `hitData` arrives **in-game** (Savant is post-game), making it a **live-pricing** asset
  rather than a carry-study one. Recommend re-scoping under that justification or dropping.
- **Separating "residual confound" from "real non-aerodynamic mechanism"** (new, from N6) — the
  closed-roof vapour survival makes this the central open question. A design that could separate
  them would need within-day or within-series variation that breaks the seasonal correlation.
