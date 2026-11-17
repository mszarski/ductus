# Ductus Notch — design log

An ink-trap grotesque, designed by eye. No reference was fitted: it starts
from the kit's neutral defaults with the grotesque terminal set. So, unlike
Ductus Sans, it carries no licensing question.

## 01 — first draft: traps by rule, the signatures

![signatures, words and the character set](01.png)

**Ink traps are a rule, not a construction** (`ductus/traps.py`,
`font.traps`). After a glyph is merged, every sharp concave corner of its
outline, where the white wedges into the ink at less than `trap_angle`
(80°), gets a triangular notch:
- its mouth sits on the two edges, `trap_mouth` (26) from the corner;
- its tip goes `trap_depth` (44) into the ink along the bisector.

So the n's and m's crotches, the d, b, p and q lobe joins, the insides of
v, w, A, M, N and V, and the forks of k and K are trapped without touching
any construction. `"skip"` leaves the commas and quotes alone, since their
dot-to-tail joint is no crotch. The stems lint measures the outline before
the traps (`CompiledGlyph.untrapped`).

**Weight.** A monoline face from three numbers in `font.py` (stem 92,
thin 78, capital stem 98): every thin and thick part is derived from them.
Other settings:
- x-height 548;
- arches with little contrast;
- curved stroke ends cut on a slant (the `sans_cut_*` angles).

**Signatures** (new `kit.define` options and controls, all defaulting to
the old outlines; the other faces are unchanged glyph for glyph):
- **Flat-footed descenders:** `g_tail="foot"` and `y_tail="foot"`
  (`y_foot_r`). g, j and y turn a tight corner into a level flag to the
  left.
- **Branched k and K:** the leg springs from the arm, away from the stem.
  That gives a Y with two trapped crotches (values only: `k_leg_x0` and
  `k_leg_y0` on the arm).
- **R:** its leg springs from the stem under the bowl, not from the bowl.
- **The angled bar:** `e_bar_tilt` (12°; the e's aperture follows the
  bar). The a's straight top rises to match (`a_bt_tilt`).
- **t:** its top cut at 50° (the face's own `t_top` terminal,
  `sans_cut_ttop`).
- **& ? @:**
  - a one-stroke looped & (`amp_style="stroke"`);
  - a ? at full weight to its end;
  - an upright @ whose inner stem runs on into the ring
    (`at_style="hook"`).

**Spacing and kerning.** Side bearings are set by eye (f, r, L, t, T, j,
J). Kerning is optical, from these outlines, with no house style:
`ductus kern examples/notch/font.py`.

Self-critique, for the next round:
- the capitals are spaced tight, and the A's trapped crossbar is busy;
- the a's tilted top reads oddly at small size;
- the G's jaw trap looks like an arrow;
- C, S, c and s ends are a little sharp;
- the figures are plain;
- it covers 66 glyphs: no accents yet, no Bold.
