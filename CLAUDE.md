# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Read `HANDOFF.md` first** for current state, latest numbers, history, open questions and
next steps (paths there are relative to `ductus/`). This file holds only durable knowledge.

## Project Overview

**Ductus** (`ductus/`) is a parametric font design language and compiler. Glyphs are
described in Python (`font.py`) as named strokes, contour parts and shared parameters;
hand adjustments live as deltas in `overrides.yaml`; the compiler emits a CFF `.otf`.
The current focus is **Ductus Sans**, a grotesque built from the same serif kit as the
original display serif. `ductus/README.md` (status, editor, benchmark, primitives table)
and `ductus/docs/sans/README.md` (sans design log) are the best long-form references.

## Layout (all under `ductus/`)

- `ductus/` the package: `skeleton/pen/profiles/junctions/contours/terminals/parts`
  (primitives), `compile.py` (compile_font), `emit.py` (build_otf), `lint.py`,
  `kerning.py` (optical auto-kerner), `overrides.py`, `proof.py`, `cli.py` (typer app),
  `bench/` (IoU/Hausdorff vs a reference), `serve/` (live editor, Starlette + websockets).
- `ductus/kits/serif.py` the genre kit (~2300 lines): every construction written once
  against a param namespace. `kit.params(...)`, `kit.define(font, P, glyphs=..., terminals=..., <style options>)`,
  terminal sets `kit.sans_set(P)` etc. Shared by the benchmark, the display serif and the sans.
- `examples/sans/` **Ductus Sans**: `font.py` (one big `kit.params(...)` call, `kit.define`
  with `terminals=kit.sans_set(P)` and grotesque options such as `g_style="single"`,
  `l_style="tail"`, `J_style="base"`, `R_leg="curve"`, `Q_style="bar"`), per-glyph
  side bearings in `font.spacing`, `kerning.json` loaded at the end of `font.py`.
- `examples/display_serif/` original high-contrast display serif (designed by eye, never fitted).
- `examples/test_font/` M1 sans test font (used by most unit tests via `tests/conftest.py`).
- `benchmarks/geist_serif/`, `benchmarks/geist_sans/` reference fetchers (+ fitted benchmark font for serif).
- `docs/` iteration sheets and logs: `docs/sans/NN.png`, `docs/display_serif/NN.png`,
  `docs/representability.md` + `docs/iterations/NN/<glyph>.png` (bench overlays; not in this sparse clone).

## Commands (run from `ductus/`; tests and `--docs` defaults use relative paths)

```bash
pip install -e ".[proof,validate,serve,bench,test]"    # Python >= 3.11; use a venv
pytest                                                  # all tests (testpaths = tests)
ductus build examples/sans/font.py -o out/              # .otf, validated by fontTools round-trip + OTS
ductus test  examples/sans/font.py                      # lints + compatibility sweep of ranged params
ductus kern  examples/sans/font.py --clearance 60 --min-abs 5   # rewrites examples/sans/kerning.json
ductus kern  examples/display_serif/font.py             # defaults: clearance 90, min-abs 10
ductus fit   benchmarks/geist_serif/font.py --glyph o --only-improve
python examples/sans/make_sheet.py NN                   # -> docs/sans/NN.png
python examples/display_serif/make_sheet.py NN          # -> docs/display_serif/NN.png
python benchmarks/geist_sans/fetch_reference.py         # Geist-Regular.woff2 into benchmarks/geist_sans/reference/
ductus bench examples/sans/font.py --reference benchmarks/geist_sans/reference/Geist-Regular.woff2 --glyphs g --note "..."
ductus serve examples/sans/font.py                      # live editor, http://127.0.0.1:8765/
python docs/make_proofs.py                              # regenerate docs/ proofs
```

`ductus bench`/`fit` fall back to the Geist **Serif** reference; pass `--reference`
explicitly for the sans (`serve` shows no reference unless given one). `ductus fit` tunes parameters only, never overrides;
always use `--only-improve` (saves only if every glyph improves and none falls off target).
Fitting helpers live in `tools/fitting/` (see its README): hard-coded absolute paths, thousands
of temp fonts written to `sw/`, and `exp.py`'s words image compares against Geist **Serif** even for the sans.

This clone uses a sparse checkout excluding `ductus/docs/iterations/` (case-collision workaround).
Do not change sparse-checkout settings or touch that folder. `SPEC.md` (rev 2) is not in the repo;
ask the user if you need it. `trajectory_classifier` was removed; it is unrelated history.

## Conventions

- **Licensing (SPEC section 8):** Geist Sans/Serif (SIL OFL) are fetched into git-ignored
  `reference/` dirs for measurement and overlays only. Never copy, trace or import their
  outlines. Anything fitted to a reference stays in `benchmarks/` and is never released.
  The display serif in `examples/display_serif/` is never fitted.
- Prefer parameters and kit options over `overrides.yaml` deltas (benchmark target is
  <= 2 overrides per glyph; the sans has none). New structure choices go into
  `kit.define` as options so both faces keep working; a kit change must keep the
  serif, the sans and the benchmark lint-clean (`tests/test_contours.py`,
  `test_junctions.py`, `test_primitives.py` parametrize over all three).
- Units are font units at upm=1000. Sans values are tuned toward Geist Sans from overlays
  and bench IoU, then rounded. Side bearings: `sb_straight`/`sb_round` plus per-glyph
  `(dl, dr)` in `font.spacing` (sans) or `@glyph(..., sb=(dl, dr))`.
- After changing outlines or spacing, re-run `ductus kern` (it measures the unkerned font).
- Each iteration: regenerate the sheet, record changes and a self-critique in the
  matching `docs/.../README.md`, and report mean IoU vs the reference in the commit
  message (e.g. "Mean IoU vs the reference 0.913 -> 0.916; lint and tests clean").
  Commit subjects are prefixed with the face: `Ductus Sans: ...`.
- `.png` files are ignored by the root `.gitignore` except under `ductus/docs/`
  (re-included by `ductus/.gitignore`); `out/` and `_build/` are ignored.

## Gotchas

- **Case-insensitive filesystems (macOS default):** bench overlays are named by glyph, so uppercase glyphs
  get a trailing underscore (`overlay_name()` in `cli.py`: `H_.png` next to `h.png`). Keep that rule for any
  new per-glyph output file, or `H.png`/`h.png` collide and break checkouts on macOS.
- **FreeType ignores the legacy `kern` table in CFF fonts.** Proofs must use `proof.gpos_kerning`
  / `render_text` (cached by path + mtime); proofs made before that fix were unkerned.
- `proof._shape` applies every GSUB type-4 ligature lookup regardless of feature; distrust odd reference renders.
- Packages are discovered (`[tool.setuptools.packages.find]`, `ductus*`); `tests/test_packaging.py` fails if a subpackage would not ship.
- Pinhole contours < 40 u² are dropped after merge (< 4 u² earlier); a real tiny mark can vanish.
- Stems lint is skipped for slanted glyphs (`font.slants`), profiled strokes and strokes with node `dw`.
- Composites inherit their base's kerning weights; combines (æ œ) take their outer parts'. Marks are drawn
  at lowercase position and lifted by cap height minus x-height on capitals.
- `font.spacing` deltas also widen empty glyphs (space). Key glyphs by name (`AE`), not character.
- Sans pitfalls from inherited serif defaults: needs `N_dy=12` (N tick drops below baseline), `at_slant=0`
  (default 14), `ced_w 55` (cedilla lint). Check inherited serif defaults when adding sans glyphs.
- Open strokes are oriented by construction (clockwise), not signed area (area flipped `r` at a sweep corner).
- Process handling: never `pkill -f` (kills its own shell); `pgrep -f` matches itself, use
  `ps -eo args | grep "^.../ductus fit"`; shell chains can hide a lint FAIL, check exit codes;
  don't `git stash` while fits run; commit after background jobs finish, not mid-run.

## Key decisions (keep unless the user says otherwise)

- **Serifs live in the terminal set, not the constructions.** A new face = a terminal set + param
  values + `kit.define` style switches. A separate "sans kit" was rejected.
- **Extend the language before adding overrides** (SPEC principle 7); the benchmark reached 0 overrides this way.
- SPEC §13 answers (in `README.md`): named-extrema bowls, Hobby skeletons (not Spiro), width profiles as
  knot curves with smoothstep, decorators not a builder, naming `glyph.instance[.stroke].node`, overrides not inherited.
- **Turning pen:** pen angle varies along strokes (node `pen_angle`, `dp` override), clamped to ±80°
  (widths spike near 90°); profiles mapped by arc length with smoothstep-eased node deltas.
- Benchmark IoU is exact on outlines (pathops) at the best offset, with guards (pathops once returned 1.007).
- **Kerning is optical, computed from our own outlines** (`kerning.py`): power mean of side-profile gaps
  (p = −32, depth 500) vs a flat `|` edge; serifs discounted by morphological opening; 2-D clearance only
  limits tightening. House style = per-glyph `[left, right]` weights fitted to the reference by ALS
  (`kern_style.json`). Rejected: copying reference kern values (licensing), an "H" partner (serifs pollute), 1-D clearance.

## Dead ends (don't repeat)

- **Sliver traps:** IoU gains from thin hairline extensions that look wrong (A toe, v top serifs, Œ bowl
  hairline inside the E). Now constrained (`A_foot_dl` −20, `v top_serif_len`, `OE_dw <= 0`). Always look at the overlay.
- Judging on zoomed single letters made the display serif worse; judge on words, keep `docs/display_serif/history.png`.
- Blind multi-glyph fit merges made glyphs worse (hence `--only-improve`).
- Reverted: `g_full` 0.57 (g self-overlap), serif inner-bracket and S-angle experiments, a reversed arch
  leg-end formula (use `n_leg_top`), an Œ trim cut that removed the E arms (bowl's right wall is now the stem).
- Sans `7`: the kit's wedge serif under the bar fails overlap lint with `seven_style="curve"`; it is skipped there.

## Working with the user

- **Show, don't just tell.** Send sheets and overlays as images after each step; they often ask "show me the sheet".
- **They judge visually**, on set words at ~80–120 px against the previous version and the reference, with
  before/after images. Numbers support the judgment but don't replace it. "Fix X" means it should *look* right.
  Their corrections: "somehow that looks worse than a few turns ago?" (keep a history, judge on words);
  "Joins all look thin, g is quite different up top" (they want real perceptual closeness, not IoU gains).
- **Keep going without check-ins** on clear iterative asks ("keep going until you fix them all"). For open-ended
  requests (e.g. "try a different style font") offer choices first. Ask before starting a new SPEC milestone.
- Answer mid-turn questions (e.g. "what branch are we on?") inline, then continue the work.
- **Report numbers exactly** (a 0.976 was once misstated as 0.975) and **push only when tests are green**
  (a commit was once pushed with a failing test).
- **Licensing:** Geist renders and data stay out of the repo (scratch only). A Geist Sans comparison image
  was committed by mistake in `179a97a` and removed in `3ac61e9`.
- **Git:** no PRs unless asked. Commits end with the session's `Co-Authored-By` trailer; model names appear nowhere else.
