# Handoff: Ductus (parametric font compiler)

Notes for a fresh session picking up the work. **Read CLAUDE.md first**: it
holds the durable rules, and wins where the two disagree. Paths are
relative to `ductus/` (the project inside this repo) unless they start
with `/`.

Repo: `mszarski/ductus`. Work branch: `claude/quirky-darwin-eqmcsa`; no PR
yet. History before the move lives in `mszarski/claude_playground` on the
same branch name.

---

## 1. Goal

**What it is.** Ductus is a Python-embedded language for describing
typefaces as strokes, parts and shared parameters. A compiler turns that
description into a real OpenType (CFF) font, and a live browser editor lets
you design with it.

The idea: generate the 90% from shared parameters, hand-own the 10% with
named-point overrides, and treat a font like software (it compiles, it has
lints and tests).

**Where the spec came from.** The user uploaded `SPEC.md` twice (rev 1, then
rev 2). **It is not in the repo**; it only existed as an upload to this
session. If the new repo should have it, ask the user to add it. Its key
points:

- **M1, foundations and editor.** Glyphs `n h m o H O space`; build a valid
  .otf; point compatibility across a `stem` 40–160 sweep; overrides stored as
  deltas on semantic names; the `ductus serve` editor; `ductus test`.
- **M2, representability.** Make the DSL expressive enough to represent a
  high-contrast display serif in the genre of Geist Serif (Vercel, OFL).
  - Metrics: UPM 1000, cap height 710, x-height 530, ascender 750,
    descender −200.
  - A benchmark harness: IoU, Hausdorff and override count per glyph.
  - Editor additions: onion-skin overlay, error heat map, stage inspector,
    grouped overrides, primitive handles.
  - An original display serif in `examples/display_serif/`.
- **Later milestones:** M3 variable fonts plus a full character set (done for
  the sans); M4 size-aware compilation (opsz, hairline rasterisation tests;
  **started**: the display serif's opsz 9–72 axis); M5 kerning and spacing from
  shape (optical kerning done); M6 rule-based derived styles (italics;
  **started**: corrected obliques for both faces, `ductus.italic`); M7
  browser-only mode via Pyodide.
- **Licensing rule (SPEC §8).** Geist is used **only for measurement and
  overlays**. Never copy, trace or import its outlines. Anything fitted
  closely to it is a derivative work under the OFL, so it must stay an
  internal benchmark under `benchmarks/` and never be released.

**What success looked like.**
- M1 done, M2 done: every benchmark glyph at IoU ≥ 0.93, Hausdorff ≤ 20 u,
  ≤ 2 overrides.
- Then, at the user's direction: a full Latin-1 display serif, pulled
  visually close to Geist Serif.
- Then a second style from the same compiler and kit (Ductus Sans, matched to
  Geist Sans).
- The user judges success **by eye on set words**, not by IoU alone.

## 2. Current state

### What works
- **Compiler pipeline.** Params → parts/glyphs → Hobby skeletons → pen
  expansion → junctions and terminals → skia-pathops merge (union minus
  cuts; cuts are unioned one by one) → spacing → CFF OTF. The font
  carries GPOS `kern`, GSUB `liga`, and a legacy `kern` table capped at
  10,920 pairs.
- **CLI:** `build`, `test`, `serve`, `kern`, `bench`, `fit`, `proof`.
- **Editor:** `ductus serve`.
- **Optical auto-kerner:** per-glyph style weights plus per-side biases.
- **Composites:**
  - `font.composite` (accents);
  - `font.combine` (æ œ);
  - `font.turn` (¿ ¡: a half turn about the ink);
  - `font.slant`.
- **Kit** (`ductus/kits/serif.py`). Grotesque style switches on
  `kit.define(...)`, all used by the sans:

  | Switches | Glyphs |
  |---|---|
  | `g_style`, `l_style`, `J_style`, `R_leg`, `Q_style` | g l J R Q |
  | `seven_style`, `fig_ends`, `one_style` | 7, 6 9, 1 |
  | `face_serifs`, `level_trim` | wedge serifs; diagonal letters |
  | `d_style`, `b_style="oval"`, `a_style="stroke"` | d q g, b p, a |
  | `y_left`, `brace_beak`, `ss_style`, `j_style` | y, { }, ß, j |
  | `paren_ends`, `chevron_style`, `amp_style` | ( ), < >, & |
  | `dot_style`, `ligatures` | dots; the fi ligature |

  Each has a serif-safe default.

### Fonts

| Font | Glyphs | Status |
|---|---|---|
| Ductus Sans (`examples/sans/`) | 183, incl. ¿ ¡ ¢; no fi ligature | Iterations 01–29 (`docs/sans/README.md`, sheets `NN.png` / `NN_sheet.png`; 19–29 are the per-glyph refits with `tools/fitting/gfit.py`). Mean IoU vs Geist Sans **0.9575** (Bold 0.9532, Light 0.9432). Kerning per master (`kerning.json`, `kerning_700.json`, `kerning_300.json`); agreement with Geist Sans corr 0.823, MAE 7.0 u |
| Ductus Display (`examples/display_serif/`) | 184, incl. ¿ ¡ ¢ | Iterations 01–34 (34: by-eye review, ¢ added). Letters ≈ 0.944 vs Geist Serif. Kerning 5,378 pairs |
| Benchmark (`benchmarks/geist_serif/`) | full kit set (184); core 16 = `CORE` | Core 16: 0.96–0.995 (mean 0.9767), 0 overrides. Whole set fitted per glyph (round 8): mean 0.936 over 122 base glyphs; side bearings fitted to Geist Serif (`spacing.json`), optical kerning with a fitted house style (agreement with Geist Serif corr 0.831); @ still 0.70 (internal only, never released) |
| Test font (`examples/test_font/`) | 7 | The M1 font |

### Ductus Sans weakest glyphs (IoU)

| Glyph | IoU |
|---|---|
| standalone cedilla | 0.46 (ç Ç ≈ 0.88) |
| ~ | 0.74 |
| ^ | 0.77 |
| @ | 0.82 (Geist's inner a leans; ours is upright) |
| tilde mark, = | 0.82–0.83 |
| quotes, comma | 0.83–0.84 (Geist's are wedges; ours are balls with tails) |
| £ | 0.84 |

Every letter and figure is now ≥ about 0.90. The visible defects found at
200–500 px have been fixed (see `docs/sans/README.md` 03–06).

### In progress
- **SPEC M3, variable weight axis.** `ductus build --variable`
  builds Ductus Sans as a CFF2 font, `wght` 300–700, with all 183 glyphs
  varying (`ductus/variable.py`, `ductus/compat.py`; `docs/sans/README.md`
  07–09).
  - The Bold and Light masters are designed against Geist Bold and Light
    (`examples/sans/master_*.json`, fitted with `tools/fitting/mfit.py`):
    Bold 0.880, Light 0.890.
  - The Bold's arches (n m h u r) were reshaped by eye against Geist Bold
    (`docs/sans/README.md` 09). Pen contrast now follows the horizontals'
    scale. Don't let IoU fits pull `n_shoulder_x` back toward 0.63 at Bold:
    that brings back the lopsided counter.
  - Each master has its own kerning (`kerning.json`, `kerning_700.json`,
    `kerning_300.json`; `ductus kern --master 700`), interpolated in the variable font.

## 3. Decisions and reasons
- **Open questions in SPEC §13** are answered in `README.md` ("Decisions on
  the open questions"):
  - named-extrema bowls, not superellipse formulas;
  - Hobby skeletons, not Spiro (tension is more direct to expose);
  - width profiles as small knot curves with smoothstep between knots;
  - decorators, not a builder;
  - naming `glyph.instance[.stroke].node`;
  - overrides are not inherited.
- **Benchmark target: IoU ≥ 0.93, Hausdorff ≤ 20 u, ≤ 2 overrides.** Set
  after `o`/`n`. IoU is exact on outlines (pathops), aligned at the best
  offset, with guards because pathops once returned IoU 1.007.
- **Prefer extending the language over overrides** (SPEC principle 7). The
  benchmark reached 0 overrides that way: the `h` overrides were later
  replaced by parameters.
- **Serifs live in the terminal set, not in the constructions.** That is why
  a sans needed only `sans_set`, monoline values and a few structural style
  switches, not a new kit. Making a "sans kit" was rejected.
- **The turning pen.** The pen angle varies along strokes (node `pen_angle`,
  the `dp` override), clamped to ±80°. Profiles are mapped by arc length with
  smoothstep-eased node deltas, which removed kinks at nodes.
- **Open strokes are oriented by construction** (built clockwise), not by
  signed area, because area-based orientation flipped `r` at the all-max
  sweep corner.
- **Kerning is optical and computed from our outlines** (`ductus/kerning.py`):
  - The distance is a power mean of side-profile gaps (p = −32, depth 500),
    compared against a neutral flat edge `|` (edge 40).
  - Serifs are discounted with a morphological opening (height 80, reach
    100).
  - 2-D clearance only limits tightening; it never pushes apart.
  - The *house style* is per-glyph weights `[as left, as right]`, fitted to
    the reference's kerning by alternating least squares regularised toward
    1 (`kern_style.json`).
  - Rejected: copying the reference's kern values (licensing, and the shapes
    differ), a neutral "H" partner (its serifs polluted the comparison), and
    1-D clearance.
- **Proofs read GPOS kerning themselves** (`proof.gpos_kerning`), because
  FreeType ignores the legacy `kern` table in CFF fonts. All proofs before
  that fix were unkerned.
- **The user decides by eye.** Display changes are judged on whole words at
  80–120 px against the previous version, with before/after images, not on
  zoomed single letters.
- **Display serif direction.** At first it was meant to be an *original*
  design (SPEC). The user later asked to pull it "much closer" to Geist Serif
  ("it really seems like there's a large perceptual difference"), and the
  values were fitted toward Geist from iteration 18 onward. **See the open
  question in §7.**
- **Ductus Sans.** The user picked "Sans-serif (grotesque)" and "Match a
  reference" (Geist Sans).

- **Judge large, then on words.** Inspect glyphs at 200–500 px beside the
  reference (`tools/fitting/look.py`, `vlook.py`): several glyphs with
  decent IoU had visible defects there (notches, ticks, slivers, a white
  hairline). Then confirm on words at 80–120 px.
- **Rebuild to the reference's construction before tuning.** Read its
  outline points (fontTools `RecordingPen`) to see how a glyph is built,
  then add a kit option with that structure. Fitting values inside the
  wrong construction plateaus. This is how the a, b d p q g, &, ß, braces,
  6 9, 1, j, t and l were fixed.

## 4. Dead ends (don't repeat)
- **"Sliver traps."** Changes that raise IoU through thin hairline extensions
  but look wrong:
  - the A's toe;
  - v top serifs;
  - the Œ's bowl hairline showing inside the E.
  These are now constrained: `A_foot_dl` −20, `v top_serif_len`,
  `OE_dw ≤ 0`. Always look at the overlay, not just the number.
- **Judging from zoomed letters made the display serif worse.** Around
  iteration 10 the user said "that looks worse than a few turns ago". The
  fix was to judge on words and keep a history sheet
  (`docs/display_serif/history.png`).
- **`g_full` 0.57** made the g overlap itself. Reverted.
- **Inner-bracket experiments and S-angle experiments** on the serif didn't
  help. Reverted (one revert broke the parens; fixed).
- **Wrong arch leg-end formula** (side convention reversed). Reverted; added
  `n_leg_top` instead.
- **Spiking pen widths when the pen angle neared 90°.** Hence the ±80°
  clamp.
- **Œ trim cut removed the E arms.** The bowl's right wall is now the stem,
  with no cut.
- **Blindly merging fit results**, like the polish fits for several glyphs
  at once, made glyphs worse. `ductus fit --only-improve` now saves only if
  every glyph improves and no on-target glyph falls off.
- **Sans `7` face wedge.** The kit's wedge serif under the bar caused an
  overlap-lint failure with `seven_style="curve"` and doesn't belong on a
  sans. It is skipped for the curved style. Moving the stroke's start point
  did not fix it.

## 5. Gotchas
- **FreeType + CFF ignore the legacy `kern` table.** Use
  `proof.gpos_kerning` / `render_text`. `gpos_kerning` is cached by
  path + mtime.
- **`proof._shape` applies every GSUB ligature lookup (type 4), whatever the
  feature.** That is probably why Geist Sans rendered `{g}` with
  corner-bracket glyphs in a comparison. Treat odd reference renders with
  suspicion.
- **`pyproject.toml` lists `packages = ["ductus", "ductus.serve",
  "ductus.bench"]` and omits `ductus.kits`.** Editable installs work; a
  regular install would miss the kit. It should be fixed.
- **Tiny-contour filters.** Pinhole contours under 40 u² are dropped after
  merge (and under 4 u² earlier). A legitimately tiny mark could vanish.
- **The stems lint is skipped for slanted glyphs** (`font.slants`), and for
  profiled strokes and strokes with node `dw`.
- **Composites inherit their base's kerning weights; combines (æ œ) take
  their outer parts'.** Marks are drawn at the lowercase position and lifted
  by cap height minus x-height on capitals.
- **Spacing table.** `font.spacing.update({...})` holds per-glyph `(l, r)`
  deltas. Empty glyphs (space) are widened by it too. `respace.py` once
  keyed Æ by its character instead of `AE`; fixed with
  `c.isascii() and c.isalpha()`.
- **`N_dy`** applies to the right stem and the clip; the sans needs
  `N_dy=12` or the N's tick drops below the baseline.
- **The sans inherited `at_slant 14`** from defaults; it is set to 0. Check
  inherited serif defaults when adding sans glyphs.
- **The cedilla needs `ced_w 55`** in the sans, or lint fails on its
  direction and overlaps.
- **Fitting scripts** (`tools/fitting/`) have hard-coded absolute paths and
  write thousands of temp fonts into `sw/`. `exp.py`'s words image compares
  against Geist **Serif**, even for the sans.
- **Process handling:**
  - Don't `pkill -f`; it kills its own shell.
  - `pgrep -f` waiters match themselves; use
    `ps -eo args | grep "^/usr/local/bin/python3.13 /usr/local/bin/ductus fit"`.
  - Shell chains can hide a lint FAIL; check exit codes.
  - Don't `git stash` while fits run.
- **This environment's stop hook demands a clean, pushed tree** at the end
  of each turn. Commit after background jobs finish, not mid-run.
- **Flat-cut terminals cut the whole glyph.** A terminal's cut is
  subtracted from every stroke in the glyph, which once cut a white line
  through the y's tail. Use a polygon or a separate terminal tag where
  another stroke passes.
- **Ranges set for the serif can clamp sans fits.** The J's ranges once
  excluded the sans's values, so fits couldn't move it. When a fit pins a
  bound, widen the range.
- **This clone is shallow and tracks only `main`.** The work branch was
  added to `remote.origin.fetch` so the stop hook sees
  `origin/claude/quirky-darwin-eqmcsa`.

## 6. The user's preferences
- **Show, don't just tell.** Send sheets and overlays as images
  (SendUserFile) after each step. They often ask "show me the sheet".
- **They judge visually.** Words at about 80–120 px, compared with the
  previous version and with the reference. Numbers support the judgment but
  don't replace it. When asked to "fix X", they mean it should *look* right.
- **Keep going without check-ins** on clear iterative asks ("keep going
  until you fix them all"). When a request is open-ended (e.g. "try a
  different style font"), offer choices first; they picked from options for
  the sans.
- **Mid-turn questions** (e.g. "what branch are we on?") get answered
  inline, then the work continues.
- **Corrections they gave:**
  - "somehow that looks worse than a few turns ago?": keep a history and
    judge on words.
  - "Joins all look thin, g is quite different up top": they want real
    perceptual closeness, not IoU gains.
  - Earlier, a figure was misstated (0.975 for 0.976) and a commit was
    pushed with a failing test. Report numbers exactly and push only when
    green.
- **Licensing.** Geist renders and data stay out of the repo (scratch only).
  A comparison image containing Geist Sans renders was committed by mistake
  in `179a97a` and removed in `3ac61e9`; it is still in history.
- **Git.**
  - Work on `claude/quirky-darwin-eqmcsa`. No PRs unless asked.
  - Every commit ends with the session's `Co-Authored-By` and
    `Claude-Session` trailers, and model names appear nowhere else.
- **Docs.** Each iteration gets a numbered sheet `docs/<font>/NN.png` and a
  README section with a short self-critique and before/after numbers.

## 7. Next steps (priority order)
1. **Open question for the user: licensing.** SPEC §8 says fitted fonts are
   internal benchmarks. Ductus Sans is fitted to Geist Sans (shapes,
   spacing, kerning style), yet it lives in `examples/`. Options: move it
   to `benchmarks/`, or diverge it deliberately before any release. See
   `ductus/docs/fitting.md`.
2. **Sans by eye at all three weights.** Most sheets show only the Regular.
   Set words in Light / Regular / Bold beside Geist and let the user mark
   what still reads wrong, including the per-weight kerning.
3. **Remaining weak glyphs** (construction, not values):
   - @ at Light (0.84) and in the serif benchmark (0.70: Geist Serif's
     inner a differs);
   - the cedilla's hook (Geist's ¸ curls up; the curled shape fits ¸ but
     hurts ç / Ç, so it was kept for ç / Ç);
   - the benchmark's ~ (contrast) and Æ (0.86).
4. **Release preparation** (a new milestone; ask first): names, vertical
   metrics, the fi ligature (the sans has none), final variable-font
   validation, browser and word-processor tests.
5. **Display serif kerning outliers:** “A, LT, AV.
6. **M4 / M6 follow-ups:** an opsz axis for the sans; true italic forms
   (single-storey a, cursive f) for the display serif as an option; review
   the italics and the text cut in words with the user.
7. **Later milestones:** M7 browser-only mode, more scripts or languages.

**Other open questions:**
- Should `SPEC.md` be added to the repo?

## 8. Pointers

### Commands (from `ductus/`)
```bash
pip install -e ".[proof,validate,serve,bench,test]"
python -m pytest tests -q            # 121 tests, ~1.5 min
python benchmarks/geist_serif/fetch_reference.py   # Geist Serif -> benchmarks/geist_serif/reference/ (git-ignored)
python benchmarks/geist_sans/fetch_reference.py    # Geist Sans 1.9.0 (npm `geist`) -> benchmarks/geist_sans/reference/Geist-Regular.woff2
ductus serve examples/display_serif/font.py --reference benchmarks/geist_serif/reference/GeistSerif-Regular.woff2
ductus bench benchmarks/geist_serif/font.py --glyphs o --note "what changed"
ductus fit   benchmarks/geist_serif/font.py --glyph o --only-improve
ductus kern  examples/display_serif/font.py                                # clearance 90, min-abs 10
ductus kern  examples/sans/font.py --clearance 60 --min-abs 5
ductus kern  examples/sans/font.py --clearance 60 --min-abs 5 --master 700   # and --master 300
python examples/display_serif/make_sheet.py 34   # next display sheet -> docs/display_serif/34.png
python examples/sans/make_sheet.py 07            # next sans sheet -> docs/sans/07.png
```

### Key files
- **Pipeline:** `ductus/compile.py`, `ductus/pen.py`, `ductus/skeleton.py`,
  `ductus/parts.py`, `ductus/contours.py`, `ductus/junctions.py`,
  `ductus/terminals.py`, `ductus/emit.py`, `ductus/lint.py`.
- **Kerning and proofs:** `ductus/kerning.py`, `ductus/proof.py`.
- **Benchmark:** `ductus/bench/` (`metrics.py`, `run.py`, `reference.py`,
  `report.py`).
- **Kit:** `ductus/kits/serif.py`, with `DEFAULTS` as
  `name: (default, (lo, hi))`.
- **Fonts:** `examples/display_serif/` and `examples/sans/`, each with
  `font.py`, `kerning.json`, `kern_style.json` and `make_sheet.py`.
- **Benchmark font:** `benchmarks/geist_serif/` (`font.py`, `fitted.yaml`,
  `overrides.yaml`).
- **Docs:**
  - `README.md` (usage, primitives, decisions)
  - `docs/representability.md` (benchmark table, iterations 01–15)
  - `docs/display_serif/README.md` (iterations 01–33) and `NN.png`
  - `docs/sans/README.md` (01–06)
  - `docs/iterations/NN/` (benchmark overlays)
- **Fitting scripts:** `tools/fitting/` (see its README). `look.py`/`vlook.py` set words beside
  Geist at any size and render parameter variants; `rs.py` is a lint-aware joint search
  for coupled moves `cd2.py` can't make.
- **Tests:** `tests/`. Fonts are parametrised in `test_contours.py`,
  `test_junctions.py` and `test_primitives.py`; `test_ends.py` covers
  punctuation, composites, slant, combine, autokern and GPOS in proofs.

### Commits (branch `claude/quirky-darwin-eqmcsa`, this repo)
| Commit | What |
|---|---|
| `0128201` | Packaging: every subpackage ships |
| `7f6d69c` | Proof shaping: liga/rlig only |
| `c74baec` | Sans 03: figures |
| `f9d1d49` | Sans 03: bowls a b d g p q |
| `f0e6f33` | Sans 03: capitals; cut-union compiler fix |
| `89eb7a3` | Kerning biases; sheet 03 |
| `45758cb` | Sans 04: a, braces, ß, ¿ ¡ |
| `ef99ebc` | Sans 05: j, f, parentheses |
| (latest) | Sans 06: leftovers |

### External resources
- **Geist fonts:** npm package `geist`, pinned to 1.9.0 in
  `benchmarks/geist_sans/fetch_reference.py`. SIL OFL 1.1. Measurement only.
- **Helvetica comparison:** Helvetica isn't on the machine.
  `/usr/share/fonts/truetype/freefont/FreeSans.ttf` (GNU FreeFont, from
  URW Nimbus Sans) stands in. Comparisons stay in scratch.
