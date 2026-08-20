"""Kalshi fee arithmetic in EXACT DECIMAL — the single source of truth.

Import this. Do NOT re-derive the formula in floats anywhere else.

    taker = roundup(0.07 * C * P * (1-P))          dollars, P in dollars
    maker = roundup(mult * 0.07 * C * P * (1-P))   mult=0.25 on designated series, $0 otherwise

Kalshi rounds UP to the next cent **on the ORDER**, not per contract — so the
per-contract fee is size-dependent and a 1-contract quote is not representative.

WHY THIS MODULE EXISTS (the desk's 15th logged instrument catch, 2026-08-07)
----------------------------------------------------------------------------
The naive float form `math.ceil(0.07*C*P*(1-P)*100)/100` overstates the fee by
exactly one cent whenever the EXACT product already lands on a whole cent,
because IEEE floats overshoot it:

    0.07*100*0.10*0.90  ==  0.6300000000000002   ->  ceil -> $0.64
    exact                    0.63                 ->        $0.63

Rounding up is correct Kalshi behaviour; rounding up FLOAT NOISE is not. Swept
across contracts x whole-cent prices, 24 of 792 combos misfired, ALL of them
OVERSTATING, and they cluster on the round lot sizes and round prices actually
traded (C=25/50/100/200/500/1000 at 10/20/40/50/60/70/80c).

DIRECTION, stated exactly (the desk got this backwards first): an overstated fee
puts computed EV BELOW true EV, so a computed GREEN is even greener under exact
fees -- GREENS stand a fortiori -- while a computed NO-GO has true EV higher than
booked, so a BOUNDARY NO-GO is what could in principle flip favourably. The bug
can only HIDE edge, never manufacture it. Max EV impact 0.20pp of stake (worst
case is the SMALLEST round stake), median 0.025pp, against >=2pp decision
thresholds -- nothing flips in practice, which is why banked nights were NOT
re-graded.
"""
from __future__ import annotations

from decimal import ROUND_CEILING, Decimal

__all__ = ["TAKER_RATE", "MAKER_MULT", "taker_fee", "maker_fee", "buy_cash_out", "sell_net"]

TAKER_RATE = Decimal("0.07")
MAKER_MULT = Decimal("0.25")


def _price(p) -> Decimal:
    """Normalise a price to DOLLARS. Units are decided by TYPE, never by magnitude:

        int   -> whole CENTS   (36  means 36c)
        float/Decimal/str -> DOLLARS (0.36 means 36c)

    A magnitude heuristic is NOT safe here: `1` is both a legal cent price and a
    legal dollar price, and guessing silently priced a 1c contract as a $1.00
    contract (fee 0 instead of 0.01) — caught by the symmetry regression test,
    which is why that test exists.
    """
    if isinstance(p, bool):                      # bool is an int subclass; reject early
        raise TypeError("price must be a number, not bool")
    d = Decimal(p) / Decimal(100) if isinstance(p, int) else Decimal(str(p))
    if not (Decimal(0) <= d <= Decimal(1)):
        raise ValueError(f"price out of range after unit normalisation: {p!r} -> ${d}")
    return d


def _roundup(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_CEILING)


def taker_fee(contracts, price) -> Decimal:
    """Exact Kalshi taker fee in dollars for the ORDER (not per contract)."""
    p = _price(price)
    return _roundup(TAKER_RATE * Decimal(str(contracts)) * p * (Decimal(1) - p))


def maker_fee(contracts, price, mult: Decimal = MAKER_MULT) -> Decimal:
    """Maker fee on a DESIGNATED series. Non-designated series are $0 — the MLB
    bucket is not publicly pinnable, so callers must decide which applies."""
    p = _price(price)
    return _roundup(Decimal(str(mult)) * TAKER_RATE * Decimal(str(contracts)) * p * (Decimal(1) - p))


def buy_cash_out(contracts, price) -> Decimal:
    """Cash out the door on a taker BUY = stake + fee. This is the desk's
    cash-at-risk accounting basis: exposure tracks cash out the door, fees
    included."""
    p = _price(price)
    return Decimal(str(contracts)) * p + taker_fee(contracts, price)


def sell_net(contracts, price) -> Decimal:
    """Net proceeds on a taker SELL = gross - fee. Exit fees net against RETURNS
    at settlement, never against the deployment cap."""
    p = _price(price)
    return Decimal(str(contracts)) * p - taker_fee(contracts, price)
