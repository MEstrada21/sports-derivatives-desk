"""Regression tests for the exact-decimal Kalshi fee helper.

Guards BOTH directions:
  * the 24 (contracts x whole-cent price) combos where the old float-ceil idiom
    overstated by exactly 1 cent MUST now come out exact;
  * the cases the old idiom got RIGHT (notably C=1 and C=10) MUST NOT change.
"""
from __future__ import annotations

import math
from decimal import Decimal

import pytest

from kalshi_fees import buy_cash_out, maker_fee, sell_net, taker_fee


def _legacy(contracts, price_c):
    """The retired float idiom, reproduced so the tests can assert on the delta."""
    p = price_c / 100.0
    return math.ceil(0.07 * float(contracts) * p * (1.0 - p) * 100.0) / 100.0


LOTS = (1, 10, 25, 50, 100, 200, 500, 1000)


def _mismatches():
    out = []
    for c in LOTS:
        for k in range(1, 100):
            if Decimal(str(_legacy(c, k))) != taker_fee(c, k):
                out.append((c, k))
    return out


def test_the_bug_existed_and_is_now_fixed():
    bad = _mismatches()
    assert bad, "expected the legacy idiom to differ somewhere — else this test is vacuous"
    assert len(bad) == 24, f"blast radius changed: {len(bad)} combos, expected 24"
    # every mismatch was an OVERSTATEMENT — the direction that HIDES edge
    for c, k in bad:
        assert Decimal(str(_legacy(c, k))) > taker_fee(c, k)


def test_exact_cent_products_do_not_round_up():
    # 0.07*100*0.10*0.90 is EXACTLY 0.63 — the canonical case that shipped wrong
    assert taker_fee(100, 10) == Decimal("0.63")
    assert _legacy(100, 10) == 0.64          # the phantom cent, preserved for the record
    assert taker_fee(100, 50) == Decimal("1.75")
    assert taker_fee(25, 20) == Decimal("0.28")


def test_genuine_roundups_still_round_up():
    assert taker_fee(100, 21) == Decimal("1.17")   # raw 1.1613
    assert taker_fee(300, 21) == Decimal("3.49")   # raw 3.4839
    assert taker_fee(150, 34) == Decimal("2.36")   # raw 2.3562


def test_small_lots_unchanged_from_legacy():
    """C=1 and C=10 had ZERO mismatches — they must stay byte-identical."""
    for c in (1, 10):
        for k in range(1, 100):
            assert taker_fee(c, k) == Decimal(str(_legacy(c, k))), (c, k)


def test_units_are_decided_by_TYPE_not_magnitude():
    """int = cents, float = dollars. The magnitude heuristic that shipped first
    silently priced a 1c contract as a $1.00 contract; this pins the contract."""
    assert taker_fee(100, 50) == taker_fee(100, 0.50)
    assert taker_fee(300, 21) == taker_fee(300, 0.21)
    assert taker_fee(1, 1) == taker_fee(1, 0.01)      # 1 CENT, not one dollar
    assert taker_fee(1, 1) == Decimal("0.01")
    with pytest.raises(ValueError):
        taker_fee(100, 150)                            # 150c is not a price
    with pytest.raises(ValueError):
        taker_fee(100, 1.5)                            # $1.50 is not a price
    with pytest.raises(TypeError):
        taker_fee(100, True)


def test_fee_is_symmetric_about_fifty_cents():
    for c in LOTS:
        for k in range(1, 50):
            assert taker_fee(c, k) == taker_fee(c, 100 - k)


def test_maker_is_a_quarter_of_taker_before_rounding():
    for c in (100, 500):
        for k in (10, 25, 50, 75):
            assert maker_fee(c, k) <= taker_fee(c, k)
            assert maker_fee(c, k) >= (taker_fee(c, k) / 4) - Decimal("0.01")


def test_cash_out_and_sell_net():
    # representative round-lot entries, worked by hand
    assert buy_cash_out(100, 10) == Decimal("10.63")
    assert sell_net(100, 21) == Decimal("19.83")
    # cash-at-risk basis = stake + entry fee, out the door
    assert buy_cash_out(150, 34) == Decimal("53.36")


def test_no_float_contamination():
    """Every return is a Decimal with exactly 2 places — never a float."""
    for f in (taker_fee, maker_fee):
        v = f(137, 43)
        assert isinstance(v, Decimal)
        assert -v.as_tuple().exponent == 2
