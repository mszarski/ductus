# Fitting scripts

These are the working scripts that fitted Ductus Sans (`examples/sans/font.py`)
to Geist Sans, copied from the session scratchpad so they are not lost. The
display serif was fitted with near-identical copies pointed at
`examples/display_serif/font.py` and Geist Serif.

Paths come from `fitpaths.py`: the project is found from the scripts'
location; scratch output goes to `$DUCTUS_SCRATCH`, defaulting to the
git-ignored `tools/fitting/_scratch/`. Fetch the reference first:
`python benchmarks/geist_sans/fetch_reference.py`. Run the scripts from
the project directory (`ductus/`).

They write to scratch:
- `sw/`: one temporary font variant per evaluation (`cd2.py`,
  `lintvar.py`). It is never cleaned up and can reach thousands of files;
  delete it freely.
- `geist_sans.otf`: the reference converted from woff2, made on first use.
- `geist_kern.json`, `kern_weights.json`: the kerning fit's data.

The reference fonts are for measurement and overlays only (SPEC §8). Never
commit them, renders of them, or data extracted from them, such as
`geist_kern.json`.

| Script | What it does |
|---|---|
| `cd2.py GLYPHS p:step ...` | Coordinate descent on the font file's `kit.params(...)` values, scoring mean IoU over `GLYPHS`. `GLYPHS` is either one string of single-letter glyph names (`"eS"`) or comma-separated names (`seven,` / `at,`). Prints `end <iou> {changes}`; it does not write the font. |
| `apply.py "{'k': v}"` | Writes those values into the font file: replaces `k=` if present, else inserts the parameter beside others with the same prefix. |
| `tidy.py` | Re-wraps runs of one-parameter lines in the font file. |
| `exp.py font.py TAG` | Per-glyph IoU plus `MEAN IoU`, and writes `TAG.otf` and `TAG.png` (words image). |
| `respace.py built.otf` | Moves side bearings in `font.spacing.update({...})` toward the reference's. Run `exp.py` → `respace.py` until it reports no changes (usually two passes). |
| `ov.sh GLYPHS [font.py]` | Overlay grid, ours vs the reference, for comma-separated glyph names → `ov.png`. |
| `lintvar.py glyphs "k=v,..."` | Lint errors and IoU for parameter variants, without editing the font. |
| `kcal.py` | Reads Geist Sans's GPOS kerning for a 68-character set → `geist_kern.json` (scratch only). |
| `kstyle.py [lambda]` | Fits per-glyph kerning style weights (alternating least squares, regularised toward 1) → `kern_weights.json`; copy it to `examples/sans/kern_style.json`. |
| `kagree.py kerning.json ...` | Correlation and mean absolute error of a `kerning.json` against Geist's kerning. |
| `cmpw.py "line§line" out.png SIZE` | Words rendered in ours and in Geist Sans, alternating rows. |
| `look.py "line§line" out.png [SIZE] [font.py]` | Each line set in ours, then in Geist Sans, at a large size: the quickest way to spot shape defects that IoU hides. |
| `vlook.py TEXT out.png SIZE "k=v,..." ...` | Geist Sans, the current font, then each parameter variant, one row each; for judging a change by eye before applying it. |
| `rs.py GLYPHS N p:scale ...` | Random joint search: Gaussian steps on several parameters at once, kept only if mean IoU improves and lint (overlaps, direction, stems) stays clean. For coupled moves `cd2.py` can't make. |
| `weak.sh` | Example batch: a `cd2` + `apply` run per glyph group, then `tidy` and `exp`. |
| `gfit.py 400\|700 GLYPH N [prefix_or_param ...] [--dry] [--wide]` | One glyph's own parameters (default prefix `GLYPH_`) at one weight. It finds every glyph those parameters touch and scores the mean of IoU − 0.001 × Hausdorff over them. It rejects candidates that change a contour count, add clustered on-curve points (folds and kinks) or fail lint. A `LOCKED` set of values chosen by eye is left alone unless named. At 700 it writes `master_bold.json`. At 400 it writes `font.py`, first pinning each master's current value so the Bold and Light don't move. `--wide` (Bold) extends each range by its width on both sides, for offsets that should grow with the stem. |
