# Exhibit 1 — Kalshi Fee Arithmetic in Exact Decimal

Two files, copied from production:

- [`kalshi_fees.py`](kalshi_fees.py) — the desk's single source of truth for Kalshi
  taker/maker fee arithmetic, in exact `Decimal`.
- [`test_kalshi_fees.py`](test_kalshi_fees.py) — 9 regression tests, including one
  that **reproduces the retired bug** and asserts on its exact blast radius.

Run: `python3 -m pytest test_kalshi_fees.py` (9 passed).

## The case law: the float-ceil phantom cent

Kalshi's taker fee is `roundup(0.07 · C · P · (1−P))`, rounded up to the next cent
**on the order** (not per contract — so a 1-contract quote is not representative of
size economics). The naive float implementation

```python
math.ceil(0.07 * C * p * (1 - p) * 100) / 100
```

is wrong in a specific, quiet way: whenever the exact product already lands on a
whole cent, IEEE floats overshoot it and `ceil` invents a cent that does not exist.
The canonical case: `0.07 · 100 · 0.10 · 0.90` is exactly `$0.63`, but the float
product is `0.6300000000000002`, and `ceil` turns it into `$0.64`. Rounding up is
correct exchange behaviour; rounding up *float noise* is not.

Swept across contract lots × whole-cent prices, **24 of 792 combos misfired — all of
them overstating** — and they cluster exactly on the round lots and round prices a
desk actually trades (25/50/100/200/500/1000 contracts at 10/20/40/50/60/70/80¢).

## Why the module reads the way it does

- **Direction analysis is written into the docstring, stated exactly** (the desk got
  it backwards on the first pass, and says so): an overstated fee puts computed EV
  *below* true EV, so a computed GREEN is even greener under exact fees — greens
  stand *a fortiori* — while only a boundary NO-GO could in principle flip. The bug
  can hide edge, never manufacture it. That asymmetry is what justified not
  re-grading historical results, and the reasoning is preserved where the next
  reader will find it.
- **Units are decided by TYPE, never magnitude**: `int` means cents, `float` means
  dollars. A magnitude heuristic is unsafe because `1` is both a legal cent price
  and a legal dollar price — and the guessing version silently priced a 1¢ contract
  as a $1.00 contract before a symmetry test caught it. The test pinning this
  contract exists *because* of that incident.
- **The tests guard both directions.** `test_the_bug_existed_and_is_now_fixed`
  re-implements the legacy float idiom, asserts it *does* differ (a regression test
  that cannot fail is vacuous), asserts the blast radius is exactly 24 combos, and
  asserts every mismatch was an overstatement. A companion test asserts the combos
  the legacy idiom got right are byte-identical — fixing a bug must not move the
  correct cases.

Small module, but it is load-bearing: every EV the desk computes on this venue runs
through these four functions, and the maker/taker split (maker = 25% of taker on
designated series, $0 otherwise) is the difference between a dead thesis and a live
one at exchange fee levels.
