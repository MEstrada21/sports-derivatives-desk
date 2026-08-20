# Exhibit 3 — The "Corn Sweat" Study: a Pre-Registered Honest Negative

> **What this exhibit is.** A complete, runnable study record: a hash-frozen
> pre-registration, three amendments, a variant ledger, the 18 analysis scripts, and
> the machine-readable result artifacts they wrote. The study asked whether Midwest
> "corn sweat" humidity measurably moves MLB scoring. It found real physics at z ≈ 13,
> a genuine unexplained anomaly it declined to over-claim, a trade that is dead by
> **one to two orders of magnitude against exchange fee levels**, and — the part worth
> showing — **four of its own conclusions retracted on the record.** Everything runs
> from public data sources.

## The crown jewel: frozen and hashed before any outcome was read

`PREREG_CORN_SWEAT.md` was written and frozen on 2026-08-09, **before any outcome data
was read** — hypotheses, endpoints, magnitudes, clustering, controls, power analysis,
multiplicity policy, and the market-gate structure, all committed in advance with a
fixed seed (20260809). Its SHA-256 is the tamper-proofing:

```
$ shasum -a 256 PREREG_CORN_SWEAT.md
a6da2b7132685c9fe220243cec8d8f957c19de6b8e35c669fa36df40d584dcc2
```

That hash is recorded in `out/PREREG_HASH.txt` and — the closing of the loop — is read
from disk at runtime by `analyze.py` and stamped into `out/results.json` as
`prereg_sha256`. Any edit to the prereg changes the hash and breaks the match, so the
document provably predates every result that cites it. **The prereg was never edited.**
When results forced corrections, they arrived as *superseding documents*, each hashed
in turn, and `out/PREREG_HASH.txt` carries the lane-close verification that every
frozen document is byte-identical to its recorded hash:

| document | sha256 (verify with `shasum -a 256`) | provenance status |
|---|---|---|
| `PREREG_CORN_SWEAT.md` | `a6da2b71…` | **FROZEN before outcomes**; never edited |
| `AMENDMENT_1_measurement_gap.md` | `fb43b481…` | honestly labelled **EXPLORATORY** — the parent pull preceded it; sign predictions committed in writing before its fits |
| `AMENDMENT_2_statcast_carry.md` | `f1be4880…` | **genuine pre-registration** — the data ask was registered in the parent prereg §6 before any results existed; this spec was hashed before the pull ran |
| `AMENDMENT_3_review_response.md` | `dda11145…` (current) | corrective response to two independent reviews; revised once, **both hashes on the record** (initial `5f3b38fb…`) — legitimate because A3 makes no pre-registered claim |
| `VARIANT_LEDGER.md` | `3873c729…` | retrospective variant accounting, labelled as the weaker form it is |

The gradient across those rows is itself the method: the same desk, in the same week,
labelled one document exploratory and another pre-registered because the *timing of
freezing relative to data* differed — and refused to blur the distinction.

## The question

A popular late-summer narrative holds that Midwest corn evapotranspiration ("corn
sweat") measurably raises humidity around corn-belt ballparks in July–August, and that
this should move MLB totals. The operator wanted it tested properly rather than traded
on vibes. The prereg restates the claim as physics before touching data: the mechanism
variable is **air density** (corn is the instrument; air is the cause), the effect is
computed exactly from temperature, humidity and surface pressure, and the
pre-registered point prediction (+0.008 pp of HR-per-BIP per °C of dew point) is
derived from standard aerodynamics *before any fit* — §3 of the prereg then shows the
HR endpoint is under-powered for that effect by ~3–4× and says so in bold, in advance.

## The discipline

- **Pre-registered before any outcome data was read** (see above). Zero stakes; the
  market stage was gated on the physics stage clearing — and never ran.
- **Sample:** 8,686 regular-season games, 2023 → mid-2026, 32 venues, 2.90M pitches,
  443k batted balls. Weather from public reanalysis (Open-Meteo ERA5) — realized
  weather, which the study itself flags as *leak-free for descriptive physics but not
  available at decision time*: any market version would need forecasts, and the study
  says its coefficients must not be carried into a live model as-is.
- **Instrument innovation — pitch break as a barometer.** Drag and Magnus force both
  scale with air density, so induced pitch break gives ~300 continuous observations per
  game instead of ~2 Bernoulli home-run events. Identification runs within
  pitcher × pitch-type × season, within park, within calendar month, with temperature
  entered explicitly — so the density coefficients come from channels a pitcher's body
  cannot respond to (barometric pressure, water-vapour content).
- **Controls that can actually fail.** Permutation nulls (weather reshuffled within
  park × month), roofed-park placebos, planted-dose recovery, and label permutation
  where treated clusters are few. The first specification (`out/results_specv1_CONFOUNDED.json`)
  was **killed by its own pre-registered permutation control** — no month fixed
  effects let seasonal temperature masquerade as density — and the respecification is
  documented as control-driven, not headline-driven.

## What it found

- **The physics is real, at high power.** Air density visibly moves the baseball: the
  pressure channel lands at **z ≈ +13** on pitch break, indistinguishable from *exact*
  Magnus proportionality (departure z = +1.73), and a Coors Field natural experiment
  (same pitchers, ~16% thinner air) independently agrees. A pre-registered follow-up
  amendment converted the under-powered binary HR endpoint to a continuous Statcast
  carry endpoint — which resolved the magnitude the binary endpoint could not, landing
  on the physics prediction.
- **A genuine anomaly was found and NOT over-claimed.** The humidity (vapour) channel
  does roughly 3× more to the ball than its air-density contribution can explain — on
  pitched *and* batted balls, surviving a closed-roof test at 83% strength. The study's
  final position: a non-aerodynamic humidity channel exists, its identity is
  unresolved, and a residual seasonal confound is a live rival explanation. "I cannot
  separate them with the data on hand, and say so."
- **The corn-specific signature is UNRESOLVED.** A corn-belt dew-point anomaly that
  initially looked confirmed became a one-season result once clustered at the correct
  unit (the season, not the park — July–August Midwest dew is synoptic, so seven corn
  parks are ~one effective draw per summer).
- **The trade is dead by one to two orders of magnitude.** Even at the upper bound of
  the carry-implied effect, the corn anomaly is worth ~0.02 runs on a game total —
  one to two orders of magnitude below exchange fee levels, and further still below
  bookmaker margins. The market stage was correctly never run: **no lines data was
  read**, because the physics gate did not clear the size threshold. The prereg
  computed this ceiling arithmetic *in advance* (§2, Stage 3) precisely so it could not
  be rationalized afterward.
- **One exploratory survivor, honestly labelled.** Dew point → strikeout rate is the
  only endpoint of six to survive family-wise (max-statistic permutation) correction.
  It is flagged as discovered-not-preregistered, its out-of-sample "replication" was
  itself later downgraded (Amendment 3 R5: split-half after pooled selection adds no
  evidence), and it is parked pending its own prereg.

## Why this is the exhibit: the study corrects itself, on the record

Amendment 3 — the response to two independent reviews — opens with a section titled
**"RETRACTIONS — things I banked that were wrong"**:

1. The corn confirmation was downgraded to unresolved (wrong clustering unit: season,
   not park).
2. A park-ranking narrative was identified as a spec artifact — and the correction
   *restored* the operator's original park list rather than the desk's revision
   (Target Field moves from rank 11 to rank 1 on the pre-registered statistic).
3. A mechanism story ("grip") was withdrawn when a spin-axis test inverted its
   prediction — release-axis consistency is unaffected, and the excess is *largest* on
   the pitches that need grip *least*.
4. A banked constant (Coors 19.3 in per kg/m³) was found non-reproducible from
   committed code and replaced with the reproducible range (15.9–18.0).

Along the way the record also preserves: an inference error caught in the desk's own
first pass (game-level clustering with only 7 treated parks overstated significance;
the fix — a corn-label permutation — was then used everywhere); a data trap caught by a
pre-specified guard (47.6% of raw Statcast rows were foul balls that never played); and
planted-dose "positive controls" **relabelled as power calibrations** once recognized
as algebraic identities that could not fail — a control that cannot fail is asserted,
not verified. A real *upstream* control, planted at raw weather before every join and
filter, was then built to replace them.

## Repro map — which script produced which result

Run order is the chain at the bottom of the study's results document. Every script is
idempotent (skip-if-written, `--force` to override), seeded (20260809), and writes
machine-readable artifacts to `out/`. Data inputs are all public sources.

| # | script | reads (source) | writes | the result it carries |
|---|---|---|---|---|
| 1 | `build_weather.py` | Open-Meteo ERA5 hourly at park coordinates + MLB StatsAPI schedule/venue metadata (via `DATA_ROOT`) | `out/game_weather.parquet`, `out/weather_stats.json` | exact moist-air density per game, decomposed into the two behaviourally-inert channels (`rho_dry`, `vapor_density_deficit`); the prereg's power inputs |
| 2 | `build_outcomes.py` | MLB StatsAPI plate-appearance + pitch archives | `out/game_pa.parquet`, `out/pitch_cells.parquet` | game outcome aggregates; pitch cells for the break instrument |
| 3 | `analyze.py` | the two builds + `out/PREREG_HASH.txt` | `out/results.json`, `out/stage2_park_residuals.csv` | Stage 1A **z ≈ +13** pressure channel + equal-and-opposite rejection; Stage 1B under-powered exactly as pre-registered; Stage 2 (superseded by #15); planted doses + permutation nulls. Spec v1's control-kill is preserved in `out/results_specv1_CONFOUNDED.json` |
| 4 | `diagnostics.py` | #3 outputs | `out/diagnostics.json` (regenerate) | spin/velocity placebos, spin-controlled break, natural-units restatement, size ceiling |
| 5 | `robustness.py` | #3 outputs | `out/robustness.json` | nonparametric 1 °C temperature bins — the vapour excess is not temperature mis-specification |
| 6 | `maxstat.py` | #3 outputs | `out/maxstat.json` | family-wise max-statistic permutation over the 6-endpoint Stage-1B family; K/PA is the sole survivor |
| 7 | `oos.py` | #3 outputs | `out/oos.json` | K-thread era split (later corrected twice: A3 R5 and the ABS-boundary re-cut in #18) |
| 8 | `run_value.py` | #3, #4 outputs | `out/run_value.json` (regenerate) | coefficients → runs → win-probability; the deadness arithmetic |
| 9 | `measurement_gap.py` | #3 outputs | `out/measurement_gap.json` | Amendment 1 corn × window DiD (station data is not missing corn humidity) |
| 10 | `cell_permutation.py` | #3 outputs | `out/cell_permutation.json` | the self-caught inference fix: corn-label permutation for a 7-treated-cluster design |
| 11 | `pull_statcast.py` | Baseball Savant via `pybaseball` (public) | per-day cache + `out/statcast_manifest.json` | idempotent, rate-limited pull; provenance manifest (755 day-queries, 879,630 rows) |
| 12 | `analyze_carry.py` | #11 cache + #3 outputs | `out/carry_results.json` | Amendment 2 primary: equal-and-opposite on carry **REJECTS** — the desk's own pre-registered prediction failed and is reported as such; foul-ball trap guard; EV/LA placebos |
| 13 | `carry_h2_2.py` | #12 outputs | `out/carry_h2_2.json` (regenerate) | carry-implied HR effect lands on the physics prediction inside the binary CI — the registered data ask delivered |
| 14 | `build_axis.py` | MLB StatsAPI pitch archive | `out/axis_cells.parquet` | circular-statistics spin-axis cells (components + resultant length R) |
| 15 | `stage2_restate.py` | #3 outputs | `out/stage2_restate.json`, `out/stage2_shape_vs_level.csv`, `out/stage2_shape_seasonclustered.json` | the R1/R2 retractions made reproducible: season clustering (CI contains zero) and shape-vs-level (Target Field rank 1) |
| 16 | `spin_axis_test.py` | #14 + #3 outputs | `out/spin_axis_test.json` | the decisive experiment: grip disfavoured (axis consistency null, pitch-family ordering inverted) |
| 17 | `roof_and_coors.py` | #3 outputs + per-game roof state (MLB StatsAPI `gameData.weather.condition`) | `out/roof_and_coors.json` | N6 roof-state split (vapour survives a *closed* roof at 83% — doubt escalated, reported) and N7 Coors regeneration (19.3 → 15.9–18.0) |
| 18 | `amendment3_audit_items.py` | #3, #16 outputs | `out/amendment3_audit.json` | exact-proportionality test (z = +1.73), ABS-boundary re-cut of the K thread, the real upstream positive control |

## Requirements and data sources

- **Python ≥ 3.10** with `numpy`, `pandas`, `pyarrow` (parquet IO). `pybaseball` is
  needed only by `pull_statcast.py`. The regressions are hand-rolled weighted least
  squares with cluster-robust SEs and fixed-effect absorption (`analyze.py`) — no
  stats-package dependency, so the estimator is fully inspectable.
- **All data sources are public:** Open-Meteo ERA5 reanalysis (hourly weather at park
  coordinates), the MLB StatsAPI (schedule, venues, plate-appearance and pitch feeds,
  roof state), and Baseball Savant Statcast via `pybaseball` (batted-ball carry).
- **Bulk caches are not shipped.** Set `DATA_ROOT` to a directory holding the
  `data/weather/` and `data/backfill/` trees (or let `pull_statcast.py` rebuild its own
  cache); the scripts re-derive everything else into `out/`. The shipped `out/*.json` /
  `*.csv` artifacts are the study's as-run results, so every number in this README can
  be checked without running anything.

## What was left out of this exhibit, and why

- **The raw results narrative (RESULTS.md) is withheld**: its market tables quote
  trading-cost economics we keep out of public artifacts. Every substantive claim in it
  is either quoted above, present in the frozen documents, or regenerable from the
  shipped code and artifacts.
- **Four as-run artifacts** (`diagnostics.json`, `run_value.json`/`.csv`,
  `carry_h2_2.json`) are omitted for the same reason; the shipped scripts regenerate
  them without the cost constants. No other script was changed in substance —
  sanitization here means relative data paths and removed fee constants, nothing that
  touches an estimate.
- **Bulk data stays home**: the per-day Statcast cache and the intermediate parquet
  tables are rebuildable from the public APIs by the scripts above.
- A separate overnight study that shares the source directory (its own light prereg
  and result cards) is not part of this exhibit.

## What this is not

This is **not an edge claim and not a tradable result** — the study's own headline is
that the trade is dead by one to two orders of magnitude, measured rather than assumed.
The coefficients **must not be carried into a live model**: the weather is realized
reanalysis published on a multi-day lag, not decision-time information, and the study
says so itself. The one surviving exploratory thread (dew point → strikeouts) is
parked, not promoted. What the exhibit supports is narrower and worth exactly what it
says: a falsifiable claim was frozen and hashed before the data could answer it, the
instruments were strong enough to catch the desk's own errors, and the errors were
retracted in writing.

The trade died. The instrument survived. The retractions are the résumé.
