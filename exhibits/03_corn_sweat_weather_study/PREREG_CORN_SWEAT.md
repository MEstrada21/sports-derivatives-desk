# PREREG — CORN SWEAT: does dew point add carry beyond temperature?

**Lane:** `research/metrics_lab/corn_sweat/`
**Tracker:** task #50. **Origin:** operator hypothesis (Mike), 2026-08-09. **Channel:** WEATHER_MECHANISM (first instance).
**Status:** frozen BEFORE any outcome data was read. Schema/coverage recon only preceded this file.
**Stakes:** ZERO. Descriptive research lane. No bet gate. Rule #10 untouched.

---

## 0. The operator's claim, restated as physics

Extreme heat → corn transpires ("corn sweat") → regional dew point spikes in the corn belt →
humid air is less dense → less drag → fly balls carry farther → more HR → totals under-priced.

**The mechanism variable is AIR DENSITY. Corn is the instrument; air is the cause.**
Dew point is itself only a proxy for vapor pressure. We have temperature, relative humidity AND
surface pressure at park coordinates, so we compute density exactly rather than proxying it:

```
e_s(T_C) = 6.1094 * exp(17.625*T_C / (T_C + 243.04))      # hPa, Alduchov-Eskridge Magnus
p_v      = (RH/100) * e_s(T)                               # vapor partial pressure
p_d      = P_surface - p_v                                 # dry partial pressure
rho      = (p_d*M_d + p_v*M_v) / (R * T_K)                 # kg/m^3, moist air
           M_d=0.0289652 kg/mol, M_v=0.018016 kg/mol, R=8.31446
T_dew    = 243.04*g/(17.625-g),  g = ln(RH/100) + 17.625*T/(243.04+T)
```

Because `M_v < M_d`, adding water vapor at fixed (T, P) LOWERS density. The operator's physics is
correct in sign. The question is entirely one of **magnitude** and **measurability**.

### Pre-registered magnitude expectation (stated before any fit)

At T=30 °C, P=1000 hPa, moving dew point 15 °C → 25 °C:
rho falls 1.14161 → 1.13542 kg/m³ = **−0.54%**, i.e. **≈ −0.054% density per °C of dew point.**

Chain to HR, using standard aerodynamics values (Nathan): −1% density ≈ +2.5 ft carry on a 400-ft
fly; +1 ft carry ≈ +1.0–1.5% relative HR rate. Therefore:

> **Predicted β_dew ≈ +0.006 to +0.009 percentage points of HR-per-BIP per °C of dew point**
> (≈ +0.15% relative HR per °C). Call the pre-registered point prediction **+0.008 pp/°C**.

For scale, temperature's own density channel is ~8–9% across a realistic 50→95 °F range — roughly
**6–8× larger than the full realistic dew-point swing.** Dew point is a second-order term on a
second-order term.

### Ball-moisture counter-channel (noted, not modeled)

Humid air also wets the *ball* (heavier, lower COR → LESS carry), which partially cancels the
density gain. MLB has run **league-wide humidors since 2022** (storage pinned ~57% RH / 70 °F), so
in our 2023–2026 window this channel is largely severed at storage — but in-game re-equilibration
is not. Net truth may be **below** the density-only prediction above. Pre-2022 literature is not
comparable for this reason.

---

## 1. Data (all already on disk; no new pulls)

| Piece | Source | Note |
|---|---|---|
| T, RH, surface pressure, wind speed/dir | `data/weather/hourly/park_id=*/month=*/` (Open-Meteo ERA5) | hourly UTC, 69 parks, 2023-02 → 2026-07 |
| first-pitch time, park, n_pa | `data/weather/game_index/*.parquet` | 10,147 games |
| PA outcomes (`play_event`) | `data/backfill/plate_appearance/` | 10,604 game-files; **no batted-ball trajectory** |
| pitch break / velo / spin | `data/backfill/pitch/` | `horizontal_break_inches`, `vertical_break_inches`, 100% populated |
| roof type, elevation | `data/weather/venue_meta.json` | 28 Open / 7 Retractable / 1 Dome |

**Regular-season filter (binding — the archive CONTAINS spring/exhibition games):** keep only the
31 MLB venues (park game-count > 100 over the window) AND drop games before each season's opener
(hard cut: month-day ≥ 03-20). Spring parks (Salt River, Surprise, Peoria, Goodyear, Arvest …) are
excluded by the venue filter.

**Weather join:** hour of first pitch, floor to the hourly grid, park coordinates. Realized weather,
not forecast — fine for a descriptive physics study; **would be a leak for any live-pricing use** and
is flagged as such (Stage 3 must use only pre-close information).

---

## 2. Endpoints — ONE primary per stage, pre-named

### Stage 1A — INSTRUMENT: does air density visibly move the ball in OUR data?

Novel use: **pitch break is a barometer.** Both drag and the Magnus force scale with air density,
so induced break responds to ρ directly, with ~300 continuous observations per game instead of ~2
Bernoulli HR events. This is a nature-supplied positive control for the whole design.

- **PRIMARY 1A:** `β_rho` from `|induced_vertical_break| ~ rho + controls`, with
  **pitcher × pitch_type fixed effects**, velocity, spin rate, season; SEs clustered by game.
- **Sign prediction:** `β_rho > 0` — denser air → MORE break.
- **Pre-registered magnitude:** break ∝ ρ to first order, so a 1% density change should move break
  ~1% of its own magnitude (≈ 0.10–0.15 in per 1% ρ on a ~10–15 in pitch).
- **Placebo 1A:** same fit on **roofed parks only** (7 retractable + Tropicana dome). Outside-measured
  density is physically severed from the ball's actual air in closed-roof games. **Prediction ≈ 0**;
  a non-zero placebo means the join is picking up something non-physical and **the design is
  confounded — we say so and stop.**

### Stage 1B — ENDPOINT: HR response, and the decomposition test

- **PRIMARY 1B:** `β_dew` = coefficient on **dew point (°C)** in
  `HR_on_BIP ~ dew_point + temp + temp² + wind_speed + park FE + season FE`
  (linear probability model on batted-ball events; SEs clustered by game).
- **Sign prediction:** `β_dew > 0`. Pre-registered point prediction **+0.008 pp/°C** (§0).
- **Placebo 1B:** roofed-park subsample; prediction ≈ 0.

- **DECOMPOSITION TEST (the falsifiable core, secondary but pre-named):** air does not know *why*
  it is thin. Decompose ρ into its temperature channel and its humidity channel and fit both:
  `HR_on_BIP ~ rho_from_temp + rho_from_humidity + ...`. If the density story is the true mechanism,
  **β on the two channels should be equal.** If the temperature channel is much larger, temperature
  is acting through a NON-density path (ball COR, bat speed, player behavior) and the humidity claim
  **does not inherit temperature's coefficient** — which is precisely the operator's implicit
  assumption. Report `Δβ = β_temp_channel − β_humid_channel` with a CI.

### Stage 2 — CORN SIGNATURE (weather-only; no outcomes)

Cross-sectional park comparison is weak (parks differ in a hundred ways). The identifying variation
is **seasonal shape**: corn evapotranspiration peaks at tasseling (mid-July → August).

- **PRIMARY 2:** within-park residual dew point after removing temperature and a smooth day-of-year
  baseline shared across all parks; statistic = **mean July 10 – Aug 31 residual dew point,
  corn-belt parks minus non-corn open-air parks in the same latitude band (38–45 °N).**
- Corn belt (operator's list): STL, CHC, CWS, CIN, DET, MIL, KC, MIN. **MIL is retractable-roof —
  flagged, and excluded from any outcome-side corn cell.**
- **Prediction:** positive (corn-belt evapotranspiration is documented meteorology). A null here
  falsifies the *corn* half of the story even if the *air* half survives.

### Stage 3 — MARKET: gated, and pre-emptively very likely unearned

Runs only if 1B and 2 both clear with CIs excluding zero. **Pre-registered ceiling arithmetic,
computed now so it cannot be rationalized later:**

```
corn-sweat dew anomaly            +3 °C   (generous)
x  beta_dew (physics)             0.008 pp/C   ->  +0.024 pp of HR/BIP
x  BIP per game                   ~52          ->  +0.0125 HR/game
x  runs per HR                    ~1.5         ->  +0.019 runs/game
x  dP/dTotal near the line        ~0.093/run   ->  +0.18 percentage points of win prob
vs two-sided hold: -110/-110 book = 4.5% total = 2.27 pp per side
                   Kalshi ~1-2%          = 0.5-1.0 pp per side
```

> **Even at full generosity the effect is ~12× too small to clear book hold and ~3–6× too small to
> clear Kalshi commission.** Stage 3 is therefore expected to be UNEARNED. Stating this in advance.

---

## 3. Power — stated before results (the decisive number)

Assumptions, all fixable without outcome data: ~8,500 regular-season games; ~52 BIP/game
(~440k BIP); HR/BIP ≈ 0.045; per-game HR-rate SD ≈ 0.032 after overdispersion; dew-point residual SD
after temp + park + month controls ≈ 3.5 °C (**to be measured from weather data and reported**).

```
SE(beta_dew) ~ 0.032 / (3.5 * sqrt(8500))  =  ~0.010 pp per degC
MDE at 80% power, alpha=.05  =  2.8 * SE   =  ~0.028 pp per degC
Physics-predicted effect                   =   0.008 pp per degC
```

> ### **This study is under-powered for the true effect by a factor of ~3–4 at the HR endpoint.**
> **A null at Stage 1B is a POWER null, not a mechanism null, and will be reported as such.**
> To resolve +0.008 pp/°C at 80% power we would need roughly **10–15× the games** (~100k+
> regular-season games ≈ 40 seasons) — or a continuous endpoint (see §6).

Stage 1A has no such problem: ~2.5M pitches, ~8,500 game clusters, continuous endpoint. The density
effect there is expected at **>15 SE**. That asymmetry is the whole reason 1A exists.

---

## 4. Controls that must run (house rules, binding)

1. **Planted-signal positive control, two doses, through the EXACT headline function:**
   - dose A = the physics prediction (+0.008 pp/°C) — expected **NOT reliably recovered**; this
     *quantifies* the underpowering rather than asserting it.
   - dose B = 5× physics (+0.040 pp/°C) — **must be recovered** with CI excluding zero, else the
     harness is broken and no null may be banked.
2. **Permutation null:** shuffle weather across games *within park × month* (preserving the
   climatology), re-run the exact primary. Must center on zero.
3. **Roofed-park placebo** (both stages) — structural severance of the mechanism.
4. **Coors:** excluded from the primary; included in a secondary leverage check. Because ρ is built
   from measured surface pressure, Coors sits ON the density curve rather than off it — but it is a
   massive leverage point, so it does not drive the headline.

## 5. Multiplicity

Pre-named primaries: **3** (1A break, 1B dew, 2 corn anomaly). Everything else — threshold scans,
heat cutoffs, park subsets, inning splits, K/BB placebos — is **exploratory** and any headline drawn
from a scan gets a **max-statistic permutation correction**, with the number of variants tried
reported. No "above 85 °F" style cutoff is a primary. The ledger records every variant.

## 6. Pre-declared data ask (independent of the result)

The binding constraint at Stage 1B is that our only carry-sensitive outcome is a **binary** HR flag.
**Statcast batted-ball data (exit velocity / launch angle / hit distance)** turns this into a
continuous endpoint and buys roughly the missing order of magnitude of power — the same physics
question becomes answerable with the games we already have. This ask is registered now so it is not
retro-fitted to a disappointing result.

## 7. Verdict vocabulary

`MECHANISM-CONFIRMED` (1A clears + placebo null) / `ENDPOINT-UNDERPOWERED` (1B CI contains both 0
and the physics prediction) / `ENDPOINT-NULL-INFORMATIVE` (1B CI excludes the physics prediction) /
`CORN-CONFIRMED` or `CORN-NULL` / `MARKET-UNEARNED`. Honest negatives reported at probe strength.

---
*Frozen 2026-08-09 before any outcome data was read.*
