# A Sports-Derivatives Research Desk — Selected Exhibits

Curated public exhibits from a private research repository: a real-time probabilistic
pricing desk for sports event markets that I built and operate. The full engine and its
data pipelines stay private; these eight exhibits are chosen to show *how the desk
works* — the code discipline, the research process, and above all the validation
culture.

**Who I am.** Michael Estrada — trader and portfolio manager with a quant background
(Master of Engineering in Financial Technology, Duke University; prior live options work), re-engaged with
quantitative modeling by building this desk from scratch. I direct AI research agents
to move at desk speed; the hypotheses, the controls, and the decisions are mine.

**The engine, in one paragraph.** A Bayesian plate-appearance estimator
(Dirichlet-multinomial shrinkage on empirical outcome rates — deliberately simple,
defended against ML challengers in a structured bake-off it won; Exhibit 8) feeds a Monte Carlo
forward simulator that prices MLB derivative markets from any game state — pregame and
mid-game, re-seeding from a live base/out/lineup state in under a second — across
moneylines, run lines, totals, boundary markets (first-3/5/7 innings), and player
props. The simulator was independently validated against an exact analytic Markov
solution (max absolute probability difference 0.00051, inside the Monte Carlo standard
error of 0.00091). Every collected market record carries a wall-clock receipt
timestamp separate from event time, so backtests reconstruct the information state at
decision time; stores are append-only; graded results are never computed against the
model's own fair value — only against real collected prices.

## The honest record (read this first)

The house line is **"sell the machine, not a profit."** This repo makes no claim of
trading profitability, and that is deliberate — the measured record is the credential:

- **Pregame edge at conventional sportsbooks: measured DEAD, reported straight.**
  Pre-registered edge tests against real collected closing lines came back negative
  across every pregame surface tested (full-game, first-5, first-3/first-7 totals).
  The market is efficient at that grain; the repo's own ledgers say so. A powered
  anchor test against the sharpest available book found the engine's in-game accuracy
  statistically indistinguishable from it — which is a statement about the market's
  efficiency, and was recorded as such, not spun.
- **Calibration, where it passes, is enumerated and bounded.** Gate-1 calibration
  (model probabilities vs realized outcomes — no odds data involved) passed on seven
  natively-priceable player-prop markets (expected calibration error 0.003–0.026), on
  a rest-of-game "no more runs" surface (ECE 0.0054, Brier skill 0.353 across ~149k
  in-game states), and on Kalshi's first-3/first-7-innings three-way winner markets
  (positive Brier skill at both boundaries, odds-free scoring).
- **Popular betting heuristics died under pre-registered tests** — ERA-differential
  fades, a series game-3 effect, run-line structural plays, a jam-reversion cell
  (killed by max-statistic permutation), first-inning-run angles. Each verdict is
  logged with its prereg.
- **The desk keeps a numbered, append-only log of its own instrument errors** — 16
  logged "instrument catches" as of August 2026, including a float-rounding phantom cent in fee
  arithmetic (Exhibit 1), a devigging artifact that briefly manufactured a
  "beats-the-close" claim (retracted), and a deduplication key that quietly inflated a
  sample size. Catching your own instrument is a first-class result here; twelve of
  the catches are written up as vignettes in Exhibit 7.
- **Method culture:** preregistration with frozen document hashes before outcomes are
  read; planted controls that are *able to fail* (a control that cannot fail is
  asserted, not verified); max-statistic permutation on any cell scan; honest
  negatives written up with the same care as positives.

The surviving, measured thesis — after all of the above — is that the engine's
in-game pricing accuracy is worth monetizing only at low-fee exchanges, and that
thesis is being resolved the slow way: a nightly zero-stakes paper program on
receipt-timestamped live ticks, graded every morning.

## Exhibits

| # | Exhibit | What it shows |
|---|---------|---------------|
| 1 | [Kalshi fee arithmetic in exact decimal](exhibits/01_kalshi_fee_module/) | Production-grade small code: an exchange fee module born from a logged instrument catch, with regression tests that reproduce the retired bug and pin its blast radius |
| 2 | [Play-grammar research program (WMRF)](exhibits/02_play_grammar_research/) | A research idea handled honestly: a niche bioinformatics paper found, its architecture mapped to NFL play-calling, then a six-family methods survey (~30 methods, kept private) commissioned to beat it — the candidate survived as the incumbent of a designed three-arm bake-off, its weaknesses named and its challengers chosen, before any model code was written |
| 3 | [The "corn sweat" weather study](exhibits/03_corn_sweat_weather_study/) | A pre-registered physical-mechanism study that confirms the physics, kills the trade by 1–2 orders of magnitude, and retracts four of its own conclusions on review — now shipped as the complete runnable record: hash-frozen prereg, three amendments, 18 analysis scripts, as-run artifacts |
| 4 | [Home-field-advantage two-reading overlay](exhibits/04_hfa_overlay/) | Encoding a judgment layer so it cannot silently collapse to one number: a grading overlay with 7 self-test controls that fail loudly if the convention is ever mis-encoded |
| 5 | [The decision ledger](exhibits/05_decision_ledger/) | A 29-day graded record of every pick fired *and declined* (615 picks, 549 counted at settlement), adversarially audited before it was believed — and labeled ~2σ, a record, not an edge claim |
| 6 | [The K-prop failure](exhibits/06_kprop_failure/) | A model that sat its pre-registered calibration exam, failed, was diagnosed to the mechanism (a rigid 5-inning starter hook, not the strikeout rate), and shipped nothing — the two-gate discipline doing its job |
| 7 | [Instrument-catch vignettes](exhibits/07_instrument_catches/) | Twelve bugs in the desk's own measurement system — each caught before it moved a real-money decision, each told symptom-to-standing-rule, several caught while everything looked fine |
| 8 | [Dirichlet-κ shrinkage](exhibits/08_kappa_shrinkage/) | The two-line conjugate formula at the engine's core, and the three pre-registered campaigns — GPU embeddings over raw identity, learned shrinkage, Optuna-tuned GBDTs, all behind planted-oracle-verified harnesses — that failed to beat it; the one apparent ML win was a stale-data artifact the gates caught (the desk's other K, in Exhibit 6, failed the other way) |

**Note on application-letter claims.** Where my application materials assert
something checkable, the exhibit backing it is here: the fee-arithmetic instrument
catch (Exhibit 1), the honest-negative study process (Exhibit 3), the encoded
grading conventions (Exhibit 4), and the graded decision log — every pick fired
*and declined*, audited — now has its exhibit (Exhibit 5). Two remaining claims —
the Polymarket market-surface study and the receipt-timestamped live collector
infrastructure — are not public exhibits and remain interview-walkthrough topics
from the private repository.

## Data sources

Everything in this repository derives from **public sources**: the MLB Stats API,
Kalshi's public market API, nflverse play-by-play data, Baseball Savant/Statcast,
and public weather reanalysis (Open-Meteo, ERA5). No proprietary or licensed vendor
data appears here.

## License

Split, by material type (see [LICENSE](LICENSE)). **Source code** and its run
artifacts are MIT — use them, fork them, ship them. **Written research** (the exhibit
write-ups, methods notes, preregistrations, and analysis narratives) is © 2026 Michael
Estrada, all rights reserved: readable and quotable with attribution, not for
republication or commercial use without permission.

*Documents in the exhibits are lightly-redacted copies of internal working documents;
references to internal task numbers, companion files, and agent lanes point into the
private repository and are left in place deliberately — they are part of how the desk
actually runs.*
