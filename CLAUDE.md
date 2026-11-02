# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
  `docs/representability.md` + `docs/iterations/NN/<glyph>.png` (bench overlays).

## Commands (run from `ductus/`; tests and `--docs` defaults use relative paths)

```bash
pip install -e ".[proof,validate,serve,bench,test]"    # Python >= 3.11; use a venv
pytest                                                  # all tests (testpaths = tests)
ductus build examples/sans/font.py -o out/              # .otf, validated by fontTools round-trip + OTS
ductus test  examples/sans/font.py                      # lints + compatibility sweep of ranged params
ductus kern  examples/sans/font.py                      # rewrites examples/sans/kerning.json
python examples/sans/make_sheet.py NN                   # -> docs/sans/NN.png
python examples/display_serif/make_sheet.py NN          # -> docs/display_serif/NN.png
python benchmarks/geist_sans/fetch_reference.py         # Geist-Regular.woff2 into benchmarks/geist_sans/reference/
ductus bench examples/sans/font.py --reference benchmarks/geist_sans/reference/Geist-Regular.woff2 --glyphs g --note "..."
ductus serve examples/sans/font.py                      # live editor, http://127.0.0.1:8765/
python docs/make_proofs.py                              # regenerate docs/ proofs
```

`ductus bench`/`fit` fall back to the Geist **Serif** reference; pass `--reference`
explicitly for the sans (`serve` shows no reference unless given one). `ductus fit` tunes parameters only, never overrides.

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
