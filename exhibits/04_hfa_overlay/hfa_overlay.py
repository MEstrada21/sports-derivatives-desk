#!/usr/bin/env python3
"""
HFA OVERLAY — the two-reading grade convention, encoded so it cannot lapse again.

WHY THIS FILE EXISTS
--------------------
The production engine has ZERO built-in home-field advantage (the desk's 9th logged
instrument catch, internal audit 2026-07-28: P(home | equal teams) = 0.50004 +/- 0.001
structural, vs 52.7% realized, n=8,659 games). Every winner-market engine
fair therefore reads ~3pp toward the AWAY side until the flag-gated HFA term lands.

The flat "-3pp on all away sides" correction was then shown to be WRONG on away
FAVORITES (13th logged instrument catch, internal audit 2026-08-02):
the engine also COMPRESSES favorites toward 0.5 (slope of engine-on-market ~0.32 in
2026). For HOME favorites compression and the missing HFA point the same way, so +3pp
accidentally fixes the graded number. For AWAY favorites they OFFSET, so raw is
accidentally calibrated and subtracting 3pp RE-INTRODUCES the bias (+3.87pp CI-clear
[+1.27, +6.48] in the away-favorite market-55-65% cell, pooled n=1,383).

The overlay is a JUDGMENT LAYER, not a measurement, and task #27 is open precisely
because the convention is unsettled (winners take +/-3pp, margins +/-1.5pp, and that
asymmetry flips thin ML-vs-run-line pair verdicts). So this module NEVER collapses to
one number: it returns both readings and the measurement status of the cell they came
from, and the renderer prints both side by side.

THE LAPSE THIS PREVENTS
-----------------------
The two-reading habit died silently when the 2026-08-07 session ended. Nights 24-29
(08-09 .. 08-14) were graded raw-only: 64 winner/margin rows, 6 of which change SIGN
under the overlay convention. Nothing enforced the habit because it lived in session
memory rather than in code. It lives here now.

USAGE
    from hfa_overlay import grade_row, render_table
    rows = [grade_row(game="COL@SF", side="SF", market="ML", price=-130, engine_p=0.5874)]
    print(render_table(rows))

    # or as a CLI over a JSONL of {game, side, market, price, engine_p, [line]}
    python3 hfa_overlay.py rows.jsonl
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# --- market taxonomy -------------------------------------------------------
# Winner markets take the full +/-3pp; margin markets take +/-1.5pp (task #27 note:
# the engine's margin error is roughly half its winner error, and pretending otherwise
# flips thin ML-vs-RL pair verdicts). Totals are largely orthogonal to HFA per the
# 07-28 audit and take NO overlay.
WINNER_MARKETS = {"ML", "F3WINNER", "F5WINNER", "F7WINNER"}
MARGIN_MARKETS = {"RUNLINE", "SPREAD", "F5SPREAD", "F3SPREAD", "F7SPREAD"}
NO_OVERLAY_MARKETS = {"TOTAL", "FGTOTAL", "F3TOTAL", "F5TOTAL", "F7TOTAL", "PROP", "MARKETC"}

WINNER_STEP = 0.03
MARGIN_STEP = 0.015

# Two-sided holds, by market, used to devig the offered price into the "market
# strength" that selects the cell. Proportional devig is forbidden on longshot-heavy
# books (the desk's 6th logged instrument catch — it inflates longshots), but these
# are near-even two-way markets where the measured-hold method is the house
# convention. The values below are REPRESENTATIVE (rounded, typical US-book holds);
# the production module carries the desk's own measured values.
MEASURED_HOLD = {
    "ML": 0.045, "RUNLINE": 0.046, "SPREAD": 0.046,
    "FGTOTAL": 0.049, "TOTAL": 0.049,
    "F5TOTAL": 0.066, "F5SPREAD": 0.065, "F3TOTAL": 0.070,
}

# --- cell status vocabulary ------------------------------------------------
MEASURED = "MEASURED"          # the 08-02 audit measured this cell directly
CARRIED = "CARRIED"            # pre-existing convention, not the measured problem, not re-measured
UNMEASURED = "CONVENTION-UNMEASURED"   # outside every cell the audit measured -> a CHOICE, not a finding
NA = "N/A"

COMPRESSION_FLOOR = 0.65       # market side >= this = unreliable zone (both readings read 8-12pp low)


def american_to_decimal(price: float) -> float:
    price = float(price)
    return 1.0 + price / 100.0 if price > 0 else 1.0 + 100.0 / (-price)


def implied_raw(price: float) -> float:
    return 1.0 / american_to_decimal(price)


def devig(price: float, market: str) -> float:
    """Measured-hold devig of a one-sided quote into market strength."""
    return implied_raw(price) / (1.0 + MEASURED_HOLD.get(market.upper(), MEASURED_HOLD["ML"]))


@dataclass
class Cell:
    adj: float
    label: str
    status: str
    note: str = ""


def classify(is_home: bool, market: str, market_prob: float) -> Cell:
    """Select the overlay cell. `market_prob` is the DEVIGGED strength of the graded side.

    Home sides always take the overlay toward home. Away sides take it away from home
    EXCEPT in the measured away-favorite carve-out (55-65% market strength), where raw
    is accidentally calibrated and applying the overlay re-introduces a CI-clear bias.
    """
    market = market.upper()
    if market in NO_OVERLAY_MARKETS:
        return Cell(0.0, "TOTALS/ORTHOGONAL", NA, "totals largely orthogonal to HFA (07-28 audit)")
    step = MARGIN_STEP if market in MARGIN_MARKETS else WINNER_STEP

    if is_home:
        if market_prob >= 0.50:
            return Cell(+step, "HOME-FAVORITE", MEASURED,
                        "compression and missing HFA point the same way; +overlay verified n=2,679")
        return Cell(+step, "HOME-DOG", CARRIED, "dog cells were not the measured problem; convention carried")

    # away side
    if 0.55 <= market_prob <= 0.65:
        return Cell(0.0, "AWAY-FAVORITE-55-65", MEASURED,
                    "raw is accidentally calibrated here; -overlay re-introduces +3.87pp CI-clear bias")
    if 0.45 <= market_prob < 0.55:
        return Cell(-step, "AWAY-45-55", UNMEASURED,
                    "BETWEEN the measured cells. The audit measured 55-65% away favorites and the dog "
                    "cells; it did NOT measure 45-55%. Applying the overlay here is a CHOICE. Neither "
                    "reading is privileged -- this is the cell that flipped BOS/MIA/KC on 08-14.")
    if market_prob > 0.65:
        return Cell(-step, "AWAY-65-PLUS", UNMEASURED,
                    "above the measured carve-out; the audit says compression swamps everything here")
    return Cell(-step, "AWAY-DOG", CARRIED, "dog cells were not the measured problem; convention carried")


@dataclass
class GradedRow:
    game: str
    side: str
    market: str
    price: float
    engine_p: float
    line: Optional[float] = None
    is_home: bool = field(init=False)
    market_prob: float = field(init=False)
    cell: Cell = field(init=False)
    engine_p_overlaid: float = field(init=False)
    ev_raw: float = field(init=False)
    ev_overlaid: float = field(init=False)
    flags: list = field(init=False)

    def __post_init__(self):
        if "@" not in self.game:
            raise ValueError(f"game must be AWAY@HOME, got {self.game!r}")
        away, home = self.game.split("@", 1)
        if self.side not in (away, home):
            raise ValueError(f"side {self.side!r} is neither team in {self.game!r}")
        self.is_home = self.side == home
        self.market_prob = devig(self.price, self.market)
        self.cell = classify(self.is_home, self.market, self.market_prob)
        self.engine_p_overlaid = min(1.0, max(0.0, self.engine_p + self.cell.adj))
        d = american_to_decimal(self.price)
        self.ev_raw = self.engine_p * d - 1.0
        self.ev_overlaid = self.engine_p_overlaid * d - 1.0
        self.flags = []
        if self.market_prob >= COMPRESSION_FLOOR:
            self.flags.append("COMPRESSION-UNRELIABLE(>=65%)")
        if self.cell.status == UNMEASURED:
            self.flags.append(self.cell.label)
        if (self.ev_raw > 0) != (self.ev_overlaid > 0):
            self.flags.append("SIGN-SPLIT")

    def verdict(self, ev: float) -> str:
        if ev >= 0.02:
            return "GREEN"
        if ev >= -0.02:
            return "VIG-CLASS"
        return "NO-GO"

    @property
    def split(self) -> bool:
        return self.verdict(self.ev_raw) != self.verdict(self.ev_overlaid)


def grade_row(**kw) -> GradedRow:
    return GradedRow(**kw)


def render_table(rows) -> str:
    """Two readings side by side. NEVER collapses to one number while task #27 is open."""
    out = [
        "| row | game | side | market | price | mkt | engine RAW | EV RAW | verdict | "
        "engine +OVL | EV OVL | verdict | cell | flags |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        mk = f"{r.market}{'' if r.line is None else ' ' + str(r.line)}"
        adj = f"{r.cell.adj:+.3f}" if r.cell.adj else "0"
        out.append(
            f"| {i} | {r.game} | {r.side} | {mk} | {r.price:+g} | {r.market_prob:.3f} | "
            f"{r.engine_p:.4f} | {r.ev_raw*100:+.2f}% | {r.verdict(r.ev_raw)} | "
            f"{r.engine_p_overlaid:.4f} ({adj}) | {r.ev_overlaid*100:+.2f}% | "
            f"{r.verdict(r.ev_overlaid)} | {r.cell.label} | {', '.join(r.flags) or '-'} |"
        )
    splits = [r for r in rows if r.split]
    unmeas = [r for r in rows if r.cell.status == UNMEASURED]
    unrel = [r for r in rows if r.market_prob >= COMPRESSION_FLOOR]
    out.append("")
    out.append(f"**{len(rows)} rows · {len(splits)} verdict SPLITS between readings · "
               f"{len(unmeas)} in CONVENTION-UNMEASURED cells · {len(unrel)} compression-unreliable.**")
    if splits:
        out.append("- **SPLIT rows (the two readings disagree on the verdict — neither is privileged):** "
                   + ", ".join(f"{r.side} {r.market}" for r in splits))
    if unmeas:
        out.append("- **CONVENTION-UNMEASURED rows** (the overlay here is a CHOICE the 08-02 audit never "
                   "measured; report both, claim neither): " + ", ".join(f"{r.side} {r.market}" for r in unmeas))
    if unrel:
        out.append("- **Compression-unreliable (market side >=65%)**: the audit says graded reads run "
                   "8-12pp LOW on BOTH sides here — flag, do not fade: "
                   + ", ".join(f"{r.side} {r.market}" for r in unrel))
    out.append("- Overlay = judgment layer, task #27 open. Totals take no overlay. "
               "Winners +/-3pp, margins +/-1.5pp.")
    return "\n".join(out)


def _selftest():
    """Controls that fail loudly if the convention is ever mis-encoded.

    Each assertion below is a claim the 08-02 audit actually makes; if someone
    "simplifies" this module into a flat away-penalty, these break.
    """
    # 1. home favorite takes +3pp (the 08-14 SF ML row)
    r = grade_row(game="COL@SF", side="SF", market="ML", price=-130, engine_p=0.5874)
    assert r.is_home and abs(r.engine_p_overlaid - 0.6174) < 1e-9, r.engine_p_overlaid
    assert abs(r.ev_overlaid - 0.0922) < 5e-4, r.ev_overlaid

    # 2. away favorite in the MEASURED carve-out takes NOTHING (the whole 13th catch)
    r = grade_row(game="NYY@TOR", side="NYY", market="ML", price=-155, engine_p=0.6019)
    assert r.cell.adj == 0.0 and r.cell.status == MEASURED, (r.cell.label, r.cell.status)
    assert r.ev_raw == r.ev_overlaid

    # 3. margin markets take HALF the winner step (task #27's asymmetry)
    r = grade_row(game="AZ@ATL", side="AZ", market="RUNLINE", line=1.5, price=-135, engine_p=0.58985)
    assert abs(r.cell.adj + 0.015) < 1e-12, r.cell.adj
    assert abs(r.engine_p_overlaid - 0.57485) < 1e-9

    # 4. totals take NO overlay and are marked N/A
    r = grade_row(game="COL@SF", side="SF", market="TOTAL", line=7.5, price=-120, engine_p=0.6140)
    assert r.cell.adj == 0.0 and r.cell.status == NA

    # 5. the 45-55% away cell is flagged UNMEASURED, not silently graded
    r = grade_row(game="BOS@PIT", side="BOS", market="ML", price=-120, engine_p=0.57365)
    assert r.cell.status == UNMEASURED and "AWAY-45-55" in r.flags, (r.cell.status, r.flags)
    assert r.split, "BOS 08-14 is a known verdict split; if this stops splitting the thresholds moved"

    # 6. compression zone raises a flag regardless of side
    r = grade_row(game="TB@ATH", side="TB", market="ML", price=-225, engine_p=0.6895)
    assert any("COMPRESSION" in f for f in r.flags), r.flags

    # 7. a side that is not in the game is a hard error, never a silent mis-grade
    try:
        grade_row(game="COL@SF", side="LAD", market="ML", price=-130, engine_p=0.5)
    except ValueError:
        pass
    else:
        raise AssertionError("side validation is not firing")
    print("hfa_overlay selftest: 7/7 controls PASS")


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
    elif len(sys.argv) > 1:
        rows = [grade_row(**json.loads(l)) for l in open(sys.argv[1]) if l.strip()]
        print(render_table(rows))
    else:
        _selftest()
        print()
        demo = [
            grade_row(game="COL@SF", side="SF", market="ML", price=-130, engine_p=0.5874),
            grade_row(game="COL@SF", side="SF", market="TOTAL", line=7.5, price=-120, engine_p=0.6140),
            grade_row(game="AZ@ATL", side="AZ", market="RUNLINE", line=1.5, price=-135, engine_p=0.58985),
            grade_row(game="BOS@PIT", side="BOS", market="ML", price=-120, engine_p=0.57365),
        ]
        print(render_table(demo))
