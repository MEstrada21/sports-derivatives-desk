# AMENDMENT 1 — measurement-gap residual test + ball-as-hygrometer feasibility

**Date:** 2026-08-09. **Parent prereg:** `PREREG_CORN_SWEAT.md`, sha256
`a6da2b7132685c9fe220243cec8d8f957c19de6b8e35c669fa36df40d584dcc2` — **NOT edited, still frozen.**
**Origin:** operator follow-up theory, relayed via team-lead.

## PROVENANCE — read this before quoting any number below

The addendum was requested "fold into the prereg BEFORE data pull." **The data pull already
happened and the parent study is complete.** These endpoints therefore **cannot be and are not
recorded as pre-registered**, and they inherit no pre-registration protection. Recording them as
pre-registered would be exactly the violation the project's `prereg-provenance-rules` standing rule
exists to prevent (an objective change is an amendment BEFORE the fit; no silent relabelling).

What IS true and does carry weight:
- The hypothesis was **specified in writing, with its sign predictions, before these particular
  regressions were run.** That is a genuine and meaningful constraint — just a weaker one than
  pre-registration.
- The endpoints are **new** (a corn × window interaction was not in the parent analysis at all), so
  this is not a re-cut of an existing result until it looks better.
- Sign predictions below are committed **before** the fits, and the placebo is named in advance.

Status of every number produced under this amendment: **EXPLORATORY / CONFIRMATORY-IN-INTENT,
requires out-of-sample replication before it means anything.**

---

## A1 — MEASUREMENT-GAP RESIDUAL TEST

**Theory (operator):** stated humidity may UNDERSTATE true park-level humidity during corn season,
because (a) weather-station siting standards deliberately avoid crops and irrigation, and (b) our
Open-Meteo values are model-grid interpolations that smooth away park microclimate. If so, the
measured dew point is an error-laden proxy and the corn-belt × July–August cell should still carry
signal after controlling everything we measured.

**Design.** Add a `corn × Jul10–Aug31` indicator to the parent spec. Park fixed effects absorb the
corn main effect; season × month fixed effects absorb the window main effect; the interaction is a
clean difference-in-differences.

**This is run on the BREAK instrument first, not on HR.** Break carries 2.9M continuous observations
against HR's ~443k Bernoulli events, and the parent study already established that HR is
under-powered for realistic effects. Running the operator's test on the under-powered endpoint alone
would guarantee an uninformative answer.

**Sign predictions, committed before fitting.** If corn-belt July–August air is genuinely more humid
than the station says, then true density is lower than measured density there, and:

| endpoint | predicted sign | why |
|---|---|---|
| **break magnitude** | **NEGATIVE** | thinner-than-measured air → less Magnus AND (via grip) less spin |
| **release spin** | **NEGATIVE** | confirmatory: understated humidity → understated grip effect |
| **HR per batted ball** | **POSITIVE** | the operator's carry channel |
| **release velocity** | **ZERO — PLACEBO** | the parent study showed velocity responds to neither density channel; if corn × window moves velocity, we have a roster/composition confound, not air |

**Honest confound statement, stated in advance and not negotiable after the fact:** a non-zero
residual in this cell is **also** consistent with *any* unmeasured corn-park-specific,
late-summer-specific factor. It **corroborates, it does not prove.** The velocity placebo is what
separates "air" from "the parks and rosters are different in August," and it is the only thing here
that can discriminate.

**Errors-in-variables note (this cuts toward the operator).** If measured dew point is a noisy
proxy for true dew point, classical measurement error **attenuates the parent study's Stage-1B
dew-point coefficient toward zero.** So the weak Stage-1 result is *partly expected* under this
theory rather than evidence against it. This does not rescue the trade — the attenuation would have
to be enormous to close a 4–12× gap to hold — but it is the correct way to read a weak Stage 1.

**Quantification.** Convert the fitted break residual into implied excess humidity using the parent
study's measured vapour-channel slope (−39.06 inches per kg/m³), and express it in °C of dew point.
This answers the operator's question in his own units: *how much wetter does corn-belt August air
behave than the station claims?*

## A2 — BALL-AS-HYGROMETER: **DATA-BLOCKED, not attempted**

Verified on disk, not assumed:
- `data/backfill/pitch/` schema carries pitch physics only (velocity, spin, break, release position).
  **No `launchSpeed` / `launchAngle` / `totalDistance`.**
- The GUMBO corpus is **pitch-event only** and is **not on local disk** — it lived on the retired
  Lambda NFS (memory `gumbo-pitch-corpus`; GPU home is now RunPod, boxes ephemeral).
- No `hitData` reference exists anywhere in `src/bbs/backfill/` or `scripts/gumbo_backfill.py`;
  the GUMBO parser walks `playEvents` but does not extract hit data.

Per instruction, **nothing was scraped and no new source was touched.** The acquisition path and its
cost are surfaced to the operator rather than acted on.

**The instinct is right, and a version of it is already running.** "Use the ball itself as the
hygrometer instead of trusting the weather station" is precisely the move the parent study made with
**pitch break** — break residuals measure effective air density at the park, in-game, with no
weather station in the loop. The batted-ball version would be *better for the carry question
specifically* (it measures the actual mechanism rather than a correlate), which is exactly why it is
the registered data ask.

## A3 — RH vs DEW POINT (teaching note the operator asked for)

**Relative humidity is the wrong variable and dew point is the right one.** RH is the ratio of actual
vapour pressure to the *saturation* vapour pressure at the current temperature, and saturation
pressure is exponential in temperature (Magnus: `e_s = 6.1094·exp(17.625·T/(T+243.04))`). So RH
confounds moisture with temperature:

- The same absolute moisture reads as **high RH on a cool morning and low RH on a hot afternoon.**
  RH falls through the day while the actual water content barely moves.
- **Urban heat island lowers RH at constant dew point** — a downtown park reads "drier" than a
  suburban one purely because it is hotter, with identical water in the air. This matters directly
  here: Target Field (downtown Minneapolis) and Comerica are the two corn-belt parks with *negative*
  dew-point anomalies in the parent Stage 2.
- **Dew point is the temperature at which the air would saturate** — a monotone function of absolute
  vapour content alone, invariant to how hot it currently is. It is the moisture variable.
- For the physics, even dew point is a proxy: the causal quantity is **vapour partial pressure**,
  and the parent study uses `vapor_density_deficit` (kilograms per cubic metre of density removed by
  water vapour) computed exactly from temperature, RH and surface pressure.

Empirically, in the parent study, both parameterisations agree in sign and significance (break:
−0.0043 in per %RH, z=−10.7 vs −38.6 per kg/m³, z=−12.8), but the vapour-density form is the one
with a physical interpretation and a testable magnitude.

---
*Amendment frozen 2026-08-09 before the A1 fits were run; A2 feasibility was checked first because
it determined scope.*
