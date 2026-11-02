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

## 04 — the a, the braces, the ß, and ¿ ¡

![iteration 04](04.png)

Each was rebuilt to Geist's construction, read from its outline points,
rather than tuned within the old one.

**a.** `a_style="stroke"`: the bowl is one pen stroke. It runs from inside
the stem along a straight top that rises about 10° into the stem, round the
left side and the bottom, and back into the stem near the baseline. The old
oval could only give a curved top. a 0.90 → 0.94.

**Braces.** `brace_beak="point"`: the arms reach the beak at an angle
(`brace_beak_a`). A filled beak continues their edges from each stroke's
square end: the outer edges meet in the tip, and the inner ones in a notch.
Before, two level square ends stacked into a blunt, notched rectangle. The
arms stop at least half their width ÷ tan(angle) short of the midline, so
the beak is valid at every setting. { } 0.81 → 0.90.

**ß.** `ss_style="bar"` takes two strokes:
- the upper bowl comes down into a level bar that stops short of the stem;
- the lower bowl starts from that bar and ends in a level foot, cut square.

ß 0.83 → 0.945.

**¿ ¡.** A new composite, `font.turn(glyph, base, dy)`, turns a glyph 180°
about its ink and moves it `dy` up. The side bearings swap, and the
contours keep their direction. ¿ and ¡ are ? and ! hung `inv_dy` (−162)
lower, as in Geist. Added to both faces.

**Also fixed on the way:**
- **t and l:** the feet were slightly wavy (the end sat above the tail's
  lowest point). `t_bot_dy` and `l_bot_dy` raise the lowest point, so the
  foot is level: t 0.971 → 0.991, l 0.963 → 0.984.
- **g:** the hook's end was a flick. It now rounds a wider bottom
  (`gs_bot_x`, `gs_t`) to an end cut nearly across the stroke, with its own
  terminal tag (`g_end`, `sans_cut_g`), separate from the y's tail. g 0.95
  → 0.96.

Mean IoU over all glyphs: 0.923 → 0.926. Kerning was regenerated: 16,442
pairs, agreement with Geist Sans correlation 0.826, MAE 6.9 u.

**Still to do.**
- The j's hook end curls; Geist's is a level foot.
- The f's hook end has a tick.
- The parentheses end in points where Geist's are cut level.
- The a's join with the stem is a little heavy, where Geist has a thin
  crotch by the spur.
- & and @ differ in shape; # and < > differ in width.

## 05 — the j, the f and the parentheses

![iteration 05](05.png)

**j.** `j_style="foot"`: the stem turns into a level foot along the
descender, cut square at the left, as Geist's does. It replaces the hook
that curled up into a tip. It is the t's tail mirrored below the baseline:
`j_foot_y`, `j_foot_x`, `j_t`. j 0.946 → 0.957.

**f.** The hook had a pinch on its underside: `f_top_dw` (−22) thinned the
stroke at the top of the arc. Its end also ran almost straight down
(−84°) into a cut, which left a tick. The hook is now even, and ends at
−20° in a vertical cut (`sans_cut_f` 0). f 0.964 → 0.973. In "ffi" and
"off" the hooks now read like Geist's.

**Parentheses.** `paren_ends="level"`: both ends take the `paren_end`
terminal, which the sans cuts level, as Geist's are cut. Before, they were
cut across the stroke and came to points. ( ) 0.907 → 0.923.

Mean IoU over all glyphs: 0.926 (0.9258 → 0.9261). Kerning was
regenerated: 16,485 pairs, agreement with Geist Sans correlation 0.825,
MAE 7.0 u.

**Still to do.**
- The parenthesis ends taper (`paren_end_w` 0.6) where Geist's keep
  more weight.
- Dots are rounded squares where Geist's are square, though square dots
  scored lower.
- The a's join with the stem is a little heavy.
- & and @ differ in shape; # and < > differ in width.
- Geist uses no fi ligature; ours joins the f's hook to the i.

## 06 — leftovers: the a's foot, & # < >, square dots, no fi ligature

![iteration 06](06.png)

- **a.** Geist's stem doesn't stand on the baseline with a spur added. It
  turns at its foot into a short level foot, cut square: the t's tail in
  small (`a_turn`, `a_tail`, `a_foot_dy`). That leaves a V notch where the
  bowl meets the stem, so the join no longer looks heavy. a 0.942 → 0.953.
- **&.** `amp_style="branch"` uses Geist's construction:
  - a straight diagonal from the leg up into the top loop;
  - round the loop, down through the crossing into the lower bowl, and
    back into the diagonal;
  - the arm, a short stroke branching off the diagonal and cut level.

  The old single stroke made the arm the lower bowl's right side.
  & 0.83 → 0.914.
- **#.** The bars now follow the slant (`hash_bar_shift`). The verticals'
  formula centred the pair half a stroke to the right of the bars; that
  bug is fixed for both faces. # 0.853 → 0.992.
- **< >.** `chevron_style="level"`: one polygon, with the arms cut
  vertically and a flat vertical tip, as Geist's are. 0.833 → 0.978.
- **Dots.** `dot_style="square"`: sharp squares sitting on the baseline,
  with no overshoot. The bullet stays round. Period and ellipsis
  0.848 → 0.983, ! 0.946 → 0.970, ? 0.928 → 0.947.
- **fi.** `ligatures=False`: Geist sets f and i apart, and so does the sans
  now.
- **@.** The ring no longer steps out below the inner stem (`at_root_dy`).
  @ 0.796 → 0.823. The rest of the gap is that Geist's inner a leans (an
  italic a inside an upright ring); not done.

Mean IoU over all glyphs: 0.926 → 0.931. Kerning was regenerated: 16,127
pairs, agreement with Geist Sans correlation 0.823, MAE 7.0 u.

**Still to do.** The weakest are now marks and small symbols: the
standalone cedilla (0.46), ~ (0.74), ^ (0.77), @ (0.82), =, the quotes and
comma (0.83–0.84), £ (0.84).

## 07 — a variable weight axis (SPEC M3, started)

![weights 300-700](07_weights.png)

`ductus build examples/sans/font.py --variable` writes a CFF2 variable font
with a `wght` axis from 300 to 700. It has named instances Light, Regular,
Medium, SemiBold and Bold, and all 182 glyphs vary. The ramp above is that
font instantiated at seven weights, including in-between ones no master
defines.

**Masters.**
- Light is the regular with every stroke thickness ×0.7, and Bold ×1.45
  (`kit.weight_master` over `kit.WEIGHT_PARAMS`). Ratios, tensions,
  positions and glyph widths are left alone.
- A few gaps grow with the strokes they separate, so the white between
  them stays (`WEIGHT_GAPS`: the quotes, ellipsis and diaeresis).
- In the &, the waist's offset from the crossing and the lower bowl's
  offset from the diagonal scale with the weight. At ×0.7 the strokes
  otherwise stopped overlapping and the counters opened.

**Compatibility.** The raw strokes are point-compatible by construction.
The merged outline is not: as strokes thicken, overlap removal and cuts
re-segment the curves, which changed the structure of 40 glyphs at ×0.7
and 55 at ×1.45. `ductus/compat.py` unifies the masters exactly:
1. Contours are matched between masters.
2. Each master's corners are aligned to the reference's, using position
   and in/out tangents, by dynamic programming over cyclic offsets.
3. Between aligned corners, every segment becomes a cubic and segments are
   split by de Casteljau at a shared set of arc-length positions.

Shapes are unchanged (area identical); only the point structure is
matched. It refuses real topology changes, such as a counter opening; the
&'s at ×0.7 was one, found this way and fixed in the design. Master
charstrings are written unoptimised, because the CFF optimiser turned
straight curves into lines in one master only.

**Not yet.**
- The Bold is only the regular made heavier:
  - glyph widths and side bearings don't grow, so it sets tight;
  - counters close up in a e s;
  - the t's foot kinks.

  A real Bold master needs its own widths, spacing and a few structural
  values; the axis machinery takes any param overrides per master.
- Kerning is the regular's, static, at every weight.
- The display serif has no axis yet.

## 08 — a designed Bold (and Light)

![weights 300-700](08_weights.png)

Geist Sans Bold and Light were fetched for measurement only (git-ignored,
like the Regular). Geist's Bold is not the Regular scaled:

| | Light | Regular | Bold |
|---|---|---|---|
| Stems | 66 (×0.79) | 84 | 150 (×1.79) |
| Horizontals | 63 (×0.79) | 80 | 119 (×1.49) |
| n / o side bearings | 82 / 46 | 80 / 44 | 66 / 37 |

The Bold thickens its horizontals less than its stems, which keeps the
counters open. Its glyphs are wider, its side bearings tighter, its
x-height 6 units taller, and its word space narrower (228 against 250).

**Masters now carry a design.**
- `kit.weight_master(params, k, kh)` scales stems by `k` and horizontals
  (`WEIGHT_H`) by `kh`.
- A master's own values and per-glyph side-bearing deltas live in
  `examples/sans/master_bold.json` and `master_light.json`.
- `variable.compile_master()` applies both.

**Fitting** (`tools/fitting/mfit.py`, `bold.sh`, `bold2.sh`). Each master
is scored against the matching Geist weight. Candidates are refused if they
change any glyph's contour count, so the masters stay interpolable.
1. Weights and proportions on the core letters (stem 150, hairline 118,
   x-height 536).
2. Every glyph's width.
3. Dots and marks.
4. The t and l tails: longer, with wider turns at Bold.
5. The a.
6. The ring.
7. The @: at ×1.79 its ring touched the inner stem and enclosed a sliver.
8. Respacing toward Geist Bold's side bearings, and the space set to 228.

| Master | Score against the matching Geist weight |
|---|---|
| Bold | 0.820 → 0.880 |
| Light | 0.887 → 0.890 |

All 182 glyphs stay compatible across the three masters.

**Still to do.**
- Kerning is the Regular's at every weight; Bold lines run slightly long.
- The Bold's weakest glyphs are marks and symbols (", cedilla, bullet, °,
  quotes, ~, _).
- The Light got only a short pass.

## 09 — the Bold's arches (n m h u r)

![Bold arches before and after](09_bold_arches.png)

The Bold's arch tops were too heavy, and the r's arm was a thick flag.
Close-ups against Geist Bold showed several causes:

- **The arch nib kept the Regular's contrast.** A pen's thin width is a
  share of its thick one, so the thin parts scaled with the stems (×1.79)
  instead of the horizontals (×1.49). `kit.weight_master` now adjusts every
  `*_contrast` so the thin width follows `kh`. The join thicknesses
  (`n/u/r_join_thin`, `d_lobe_thin_b`) moved into `WEIGHT_H`.
- **A lopsided counter.** The shoulder sat far right (`n_shoulder_x` 0.625).
  At Bold the thick nib can't follow so tight a turn, so the counter rose
  in a straight line and then turned sharply into the leg. Bold now uses
  `n_shoulder_x` 0.52, `n_tension` 0.85 and `n_join_angle` 65.
- **A hook where the arch met the leg.** The leg stem's square top stood
  above the point where the arch turns vertical, so it cut into the curve.
  Bold now uses `n_leg_top` 0.5, so the stem starts where the arch ends,
  and `n_out_y` 0.7. The u had the same problem mirrored (`u_leg_top`).
  Its cup nib is now level (`u_angle` 0), which removes a dimple at the
  join.
- **A 1-unit crack.** `head_inset_cut` ran even with `head_inset` 0 and
  left a 1-unit slit between the stem and the arch (n, m, r). It was
  invisible in the Regular but showed in the Bold. With no inset, the cut
  now sits above the glyph and removes nothing. It isn't skipped, because the
  outline structure must not depend on a parameter's value. The Regular's score is unchanged (0.9311).
- **A tooth on the m.** Its second arch joined the first one's leg while
  that leg was still curving. The new kit parameter `m_join_dx` (default 0;
  −20 at Bold) moves the join onto the curve.
- **The r's arm.** It now leaves the stem lower (`r_join_at` 0.62, angle
  65), with a long taper (0.9) and a level end (`r_dir` −5). The underside
  is now a smooth concave curve.

These choices were made by eye. The fitter preferred the old shapes on
IoU: n/m/h/u lost about 0.03 each, and the Bold went from 0.8804 to
0.8800 against Geist Bold. Light stays at 0.8903. A refit of the arch
widths found nothing better.

**Self-critique.** The u's bowl is still a little flat on the right where
it meets the stem. The Bold also sets slightly wider than Geist Bold.

## 10 — the Bold's s, r, v, w

At Medium and Bold the s, r, v and w still looked wrong. Geist Sans Medium
and SemiBold are now fetched too, for measurement only, so the Medium can be
checked against the real thing.

The Medium matched Geist Medium closely. It only carried the Bold's faults
at half strength, so the fixes are all in `master_bold.json`:

- **s.** The stroke was too heavy for its tight turns. The inner offset
  folded where the bowls turn, leaving kinks inside them. These read as
  facets and nubs, and the Medium inherits them. Fixes:
  - rounder sides (`s_left_t`/`s_right_t` 0.85);
  - the top node moved right and the bottom node left (0.55 / 0.45),
    which widens the turns;
  - terminals refit lower and higher (`s_t1_y` 0.68, `s_t2_y` 0.315).

  The s goes from 0.872 to 0.944 against Geist Bold.
- **r.** The arm is higher and thicker (`r_y` 0.875, `r_end_w` 1.15), with
  a shorter taper. A fit pushed `r_dir` to −11, which put a wave in the
  arm's top edge; it is kept at −6. The r scores 0.943 (was 0.927).
- **v, w.** Diagonal thicknesses and vertex height were refit. The w is
  narrower (662).

The Bold scores 0.8800 → 0.8816 against Geist Bold.

**Self-critique.**
- The s keeps a short vertical flat inside each bowl. It is invisible at
  text sizes.
- The e's terminal is still a wedge where Geist cuts it level.
- Lines still set slightly long at Medium and Bold.

## 11 — the r is the n's arch, cut square

The Bold r still looked wrong: its arm was a flag rising in a straight
diagonal from a deep notch. Geist's r is the top of its n: the arm leaves
the stem at the top, rounds over a shoulder level with the x-height, and
ends in a square cut. A single curve from the join can't make that shoulder.
A steep start makes the thick pen bulge above the x-height.

New kit option `r_style="arch"` (the sans uses it; `"ear"` is the default,
so the serif and the benchmark are unchanged). The r draws the n's arch,
with its own values where Geist's r differs from its n:

- width `n_width + r_arch_dw` (the arch is wider, so the cut lands on the
  level part of the shoulder);
- its own join (`r_join_at/thin/angle`), lower than the n's, which gives a
  smooth concave underside;
- its own taper (`r_taper_len`): the taper is a share of arc length, and
  this arch is much longer than the n's;
- extra weight at the shoulder (`r_arch_sdw`), kept inside the x-height.

The arch is then cut square at `r_width`. `arch()` gained `shoulder_dw`,
`taper` and `join_at` arguments; their defaults leave n, m and h unchanged.

| r | ear (before) | arch |
|---|---|---|
| Regular vs Geist Regular | 0.943 | 0.9348 |
| Bold vs Geist Bold | 0.943 | 0.932 |

The IoU is a little lower, but the outline now follows Geist's at every
weight. Mean IoU: Regular 0.9311 → 0.9310, Bold 0.8816 (unchanged),
Light 0.8903 → 0.8904. Kerning re-run.

**Self-critique.** The Bold a's counter looks pinched in words ("rar").
That is next.
