# Ductus Sans

A grotesque sans-serif built with the same compiler and the same kit
(`ductus/kits/serif.py`) as Ductus Display. It is matched to Geist Sans
(OFL-1.1, Vercel): values are tuned from overlays and the bench's IoU, then
rounded. No outlines are copied.

Source: `examples/sans/font.py`. Sheet: `docs/sans/NN.png`
(`python examples/sans/make_sheet.py NN`). Kerning: `ductus kern
examples/sans/font.py` writes `examples/sans/kerning.json`. Reference:
`python benchmarks/geist_sans/fetch_reference.py`; it is git-ignored and
used for measurement only.

## 01 — a sans from the serif kit

The kit's constructions are style-neutral: arches, a and b lobes, bowls,
the s spine, diagonals, the cap bowls, composites, spacing and auto-kerning.
The serifs live in the **terminal set**. So the sans is mostly three
changes:

1. **`kit.sans_set(P)`**, a new terminal set with no serifs. Stems end
   square; diagonals, apices and vertices are cut flat (horizontally).
   Curved strokes' ends are cut at `sans_cut_*` angles.
2. **Monoline values**, measured off Geist Sans: stem 84, horizontals and
   former hairlines about 76, round sides × 1.05, and the joins and lobes
   at near-stem weight. Several of the kit's ranges were widened to allow
   them.
3. **Grotesque options**, new structure choices in `kit.define`:
   - `g_style="single"`: the single-storey g (the d's lobe on a stem that
     runs into a hook).
   - `l_style="tail"`: the l turns into a tail, as the t does.
   - `J_style="base"`: the J turns along the baseline and back up.
   - `R_leg="curve"`: the leg bends down to stand upright.
   - `Q_style="bar"`: a straight bar across the bowl's lower right.
   - `dot_square`: rounded-square dots.
   - `colon_dy`: the colon's upper dot set lower.
   - `N_dy`: the N's diagonal and right stem stand on the baseline.

The values were then fitted by the same coordinate searches as the serif.
Each glyph's parameters were searched against Geist Sans: weights first,
then the lowercase, capitals, figures, punctuation, symbols, accents and
Æ Œ Ø ß. Side bearings come from Geist Sans's, and the word space is
250 u. Kerning comes from the optical kerner with its default settings
(6,590 pairs; no style weights yet).

**A kit bug found on the way.** The B's two bowls each kept only half a
hairline at the waist, so their counters met and the waist pinched to a
point at the stem. Each bowl now keeps a full hairline wall. That took the
sans B from 0.89 to 0.95 and the serif's from 0.93 to 0.95.

Against Geist Sans: all 175 glyphs 0.912, the 52 letters 0.937. Weakest:
- standalone cedilla 0.38 (ç and Ç are 0.89–0.90);
- £ 0.61, ~ 0.72, 7 0.76, ^ 0.77;
- @, ? and g 0.79–0.80;
- { } and & 0.81–0.82; 8 0.82.

The sans font is linted, compatibility-swept and checked at its range
extremes in the test suite, alongside the serif.

## 02 — the weakest glyphs, and Geist's kerning style

![iteration 02](02.png)

**Glyphs.** New kit options, each fitted against the reference:
- `eight_overlap`: the 8's bowls now meet in a shorter waist;
- `seven_style="curve"`: the 7's diagonal is a bowed pen stroke, with no
  face wedge under the bar;
- a parameterised £: foot, rise, top, ear end, bar extent and base weight;
- `gs_dfar` for the single-storey g's bowl.

The searches also covered ~ ^ ç ? @ { } &.

| Glyph | Before | After |
|---|---|---|
| ? | 0.79 | 0.93 |
| 8 | 0.82 | 0.93 |
| 7 | 0.76 | 0.88 |
| £ | 0.61 | 0.84 |
| & | 0.82 | 0.83 |
| g | 0.80 | 0.81 |
| standalone cedilla | 0.38 | 0.46 |

The cedilla is a 60-unit mark, so a few units of offset cost a lot of
IoU; ç and Ç are 0.87–0.89. Mean IoU over all 175 glyphs rose from 0.913
to 0.916.

The overlays show ~ ^ @ and { } (0.74–0.81) already following the
reference closely. What remains is stroke-end angles and a slightly
different ~ curve.

**Kerning style.** Geist Sans kerns heavily: 2,525 of the 4,624
letter/punctuation pairs measured. The display serif kerns far fewer. The
per-glyph style weights in `kern_style.json` (`[as left, as right]`) are
least-squares fits to Geist Sans's kerning, regularised toward 1. Generated
with `ductus kern examples/sans/font.py --clearance 60 --min-abs 5`, giving
9,094 pairs.

| Agreement with Geist Sans | Correlation | MAE |
|---|---|---|
| Letter pairs, before | 0.57 | 14.8 u |
| Letter pairs, now | 0.68 | 12.1 u |
| All pairs, before | 0.56 | 11.6 u |
| All pairs, now | 0.71 | 8.9 u |

Key pairs, ours / Geist:

| Pair | Ours | Geist |
|---|---|---|
| To | −70 | −80 |
| AV | −105 | −106 |
| P. | −110 | −110 |
| Yo | −75 | −70 |
| Wa | −50 | −44 |
| TA | −65 | −90 |
| LT | −95 | −140 |

The words comparison against Geist Sans is not committed, because renders
of the reference stay out of the repo. To regenerate it, run
`tools/fitting/cmpw.py`. Geist also tucks a
few pairs our profile kerner leaves alone, such as rn −40 and Fl −20.

## 03 — judged large: structural fixes, and kerning with per-side bias

![iteration 03](03.png)

**How the problems were found.** The words were rendered at 200–500 px
beside Geist Sans (`tools/fitting/look.py` and `vlook.py`; the renders
stay in scratch). Several glyphs with decent IoU had visible defects:
- the 6 and 9 ended in a serif's wedge face;
- the d, q, g, b and p had V notches and an S-wave crown where a lobe
  hung on the stem;
- the y had a white hairline through its tail;
- spikes poked past the baseline or cap height on N and W;
- the r ended in a thin beak, and the t and l tails curled up;
- the G had a stub, and the U a dent.

**New kit options**, so the serif keeps its own constructions:

| Option | Glyphs | What it does |
|---|---|---|
| `fig_ends="cut"` | 6 9 | The hook turns down and ends in a plain cut. Its root is a parameter and never steps out past the bowl. |
| `one_style="arm"` | 1 | A curved arm instead of a diagonal flag. |
| `face_serifs=False` | 2 E F L T Z z 7 Æ Œ G | No vertical-face wedge serifs, and no beard on the G. |
| `d_style="bowl"`, `b_style="oval"` | d q g, b p | An oval overlapping the stem. The g's bowl sits higher (`gs_bowl_b`). |
| `a_style="bowl"` | a | A tilted oval, with Geist's square spur at the stem's foot. |
| `y_left="poly"` | y | The thick arm is a parallelogram, so no flat cut crosses the tail. |
| `level_trim` | A K M N V W X Y Z k v w x z | Cut level at the baseline and cap/x-height. |

The 2's diagonal is trimmed at the base's left end in both faces.

**A compiler bug.** Cuts were filled together by winding number. Two
overlapping cuts drawn in opposite directions therefore cancelled where
they overlapped, and left ink there. The N's diagonal clip lost its
fragment that way in both faces. Cuts are now unioned one by one. Only 6 of
379 glyphs across the three fonts changed (N and Ñ in both faces, and
sub-unit changes to the serif's G and d).

**Values.**
- The r's arm and the t and l tails keep their full weight to a level end.
- The e's aperture cut is flatter and its bar runs flush with the bowl.
- The J's ranges now cover the baseline hook (the sans sat outside them,
  so fits could not move it).
- The W is narrower (its width range now goes down to 700).

Per-glyph IoU, before → after:

| Glyph | Before | After |
|---|---|---|
| d | 0.91 | 0.98 |
| q | 0.89 | 0.98 |
| g | 0.81 | 0.95 |
| b | 0.94 | 0.98 |
| p | 0.93 | 0.97 |
| 6 | 0.88 | 0.95 |
| 9 | 0.85 | 0.94 |
| 1 | 0.89 | 0.96 |
| J | 0.78 | 0.97 |
| W | 0.89 | 0.96 |
| l | 0.92 | 0.96 |
| r | 0.91 | 0.94 |
| a | 0.86 | 0.90 |

Mean IoU over all 175 glyphs: 0.916 → 0.923.

**Kerning.** The style weights only scale our optical measure, so pairs it
sees as neutral (rn, xo, Fl) could not be kerned. Each glyph's style can now
carry two more numbers, a bias as left glyph and a bias as right glyph,
added to its pairs' kerns. These act like the class kerns a type designer
sets. Punctuation-only pairs take none.

The fit (`tools/fitting/kstyle.py`) regularises the biases toward 0.
On 30% of the pairs held out of the fit, correlation with Geist's kerning
went from 0.615 (weights only) to 0.760.

| Agreement with Geist Sans | Iteration 02 | Now |
|---|---|---|
| All pairs, correlation | 0.705 | 0.826 |
| All pairs, MAE | 8.9 u | 7.0 u |
| Letter pairs, correlation | 0.676 | 0.817 |

Ligatures now kern as their outer components do, which closes the
f + f_i gap. The legacy `kern` table keeps the strongest 10,920 pairs, its
format's limit; GPOS carries all 16,030. Generated with `ductus kern
examples/sans/font.py --clearance 60 --min-abs 5`.

**Still to do.**
- The a's bowl top is a curve where Geist's is a straight diagonal.
- The U has a slight notch where its cup meets the right stem (visible
  above about 300 px).
- ß, & and @ differ in shape.
- The braces have a notched beak.
- # and < > differ in width.
- ¿ and ¡ are missing.
- The ff join leaves a slight gap.
