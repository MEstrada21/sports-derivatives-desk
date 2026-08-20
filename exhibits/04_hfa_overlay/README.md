# Exhibit 4 — The Two-Reading HFA Overlay: Encoding a Judgment Layer So It Cannot Lapse

One file, copied from the desk's nightly grading stack:

- [`hfa_overlay.py`](hfa_overlay.py) — the home-field-advantage grading overlay,
  with 7 built-in self-test controls.

Run: `python3 hfa_overlay.py --selftest` (7/7 controls PASS), or with no arguments
for the selftest plus a demo grading table.

## The story

Two logged instrument catches collide in this module:

1. **The engine has zero built-in home-field advantage** (audit, 2026-07-28:
   P(home | equal teams) = 0.50004 ± 0.001 structurally, vs 52.7% realized across
   8,659 games). So every winner-market fair value reads ~3 points toward the away
   side, and a grading overlay adds it back.
2. **The flat correction is wrong on away favorites** (audit, 2026-08-02): the
   engine *also* compresses favorites toward 50%. For home favorites the two errors
   point the same way, so +3pp fixes the number. For away favorites they offset —
   raw is accidentally calibrated, and "correcting" it re-introduces a CI-clear
   bias.

The result is a cell map where some cells are MEASURED, some carry an unverified
CONVENTION, and one (away sides at 45–55% market strength) is explicitly
**CONVENTION-UNMEASURED** — applying the overlay there is a choice, not a finding.
The overlay is a judgment layer, and the module refuses to pretend otherwise: it
**never collapses to one number**. Every graded row returns both readings (raw and
overlaid), the cell's measurement status, and a SIGN-SPLIT flag when the two
readings disagree on the verdict — and the renderer prints both, side by side, with
neither privileged.

## Why it exists as code rather than habit

The two-reading convention originally lived in session memory — and died silently
when a session ended. Six nights of grading ran raw-only before the lapse was
caught; 6 of 64 winner/margin rows changed sign under the convention. The fix was
not a reminder; it was this module. The docstring says it plainly: *"Nothing
enforced the habit because it lived in session memory rather than in code. It lives
here now."*

The 7 self-test controls are each a claim the underlying audit actually makes —
home favorite takes +3pp; the measured away-favorite carve-out takes nothing;
margin markets take half the winner step; totals take none; the unmeasured cell is
flagged, never silently graded; the compression zone (market side ≥65%) raises an
unreliability flag; an invalid side is a hard error, never a silent mis-grade. If
anyone ever "simplifies" the module into a flat away-penalty, they fail loudly.

*Note for this public copy: the two-way hold constants used for devigging are
representative rounded values; the production module carries the desk's own measured
values. References to internal task numbers point into the private repository.*
