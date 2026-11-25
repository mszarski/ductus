# Tools

## The command line

Every command takes the path of a font module. Run `ductus <command> --help`
for every option.

| Command | Does |
|---|---|
| `ductus build FONT -o out/` | Compiles a static `.otf` and validates it (fontTools round trip, and OTS with the `validate` extra). |
| `ductus build FONT --variable` | Builds the variable font from `font.variable`, and reports any glyph held static. |
| `ductus build FONT --italic` | Builds the italic from `font.italic`; add `--variable` for a variable italic. |
| `ductus build FONT --set stem=120` | Builds with one-off parameter values. |
| `ductus build FONT --sweep stem=40,160` | Also checks the outlines stay point-compatible across the sweep. |
| `ductus build FONT --json` | Also writes the `CompiledFont` as JSON. |
| `ductus test FONT` | Runs every lint, and sweeps each ranged parameter to both ends. |
| `ductus kern FONT` | Optical kerning into `kerning.json`; `--master V` for a master, `--italic` for the italic. |
| `ductus proof FONT -o proof.png --setting "Bold:stem=150"` | Draws a contour sheet, one row per setting. |
| `ductus serve FONT` | Opens the live editor (below). |
| `ductus bench FONT --reference REF` | Measures the font against a reference font (below). |
| `ductus fit FONT --glyph o --only-improve` | Tunes parameters toward a reference (below). |

The `ductus test` lints:
- **Overlaps:** no self-intersections left after the merge.
- **Contour direction:** outer contours counter-clockwise, counters
  clockwise.
- **Stems:** every vertical stroke measures the stem it was drawn with.
- **Overrides:** every override still names a point that exists.
- **Compatibility** across the parameter sweep.

## The live editor

```bash
ductus serve examples/notch/font.py               # http://127.0.0.1:8765/
ductus serve examples/sans/font.py --reference path/to/reference.woff2
```

It recompiles on every change: a full compile takes 65–90 ms after a
parameter change, and about 10 ms per glyph while dragging. `font.py` and
`overrides.yaml` are watched, so saving either in your own editor updates
the preview. A broken `font.py` shows an error and keeps the last good
result.

- **Sliders** for every ranged parameter, with presets. *Copy* puts the
  current values on the clipboard as Python. The editor never rewrites
  `font.py`.
- **The canvas** shows the glyph in context, with metrics and its skeleton.
  Click a skeleton point for handles:
  - drag the point (`dx`, `dy`);
  - drag ◆ to turn the stroke's direction (`da`, ⇧ snaps to 15°);
  - drag □ to change its width (`dw`);
  - press `,` and `.` to change tension (`dt`);
  - turn on *Outline pts* to move expanded points;
  - drag the dashed lines to change side bearings.
- **Handles** puts orange arrows on primitive parameters: serif length,
  join height, bowl walls and so on. Dragging one writes a per-glyph
  parameter override.
- **The inspector** shows every value at the selected point, the glyph's
  overrides, and warnings for overrides that no longer match a point.
- **Undo and redo** (⌘Z, ⇧⌘Z); a whole drag is one step.
- **Text** you type is set in the freshly compiled font, with a waterfall
  and a download button.
- **With `--reference`**, the reference glyph is drawn over yours. *Heat*
  colours your outline by its distance to it, and the inspector shows live
  IoU and Hausdorff.

Every edit is written to `overrides.yaml`.

## The browser editor

`web/` runs the whole compiler in the browser, with nothing to install:
- **Compiler:** Pyodide, in a Web Worker, so the page stays responsive.
- **Overlap removal:** Paper.js, since skia-pathops has no browser build.

```bash
python web/build.py                   # the wheel, the example faces and the driver into web/_build/
python -m http.server -d web 8000     # then open http://localhost:8000/
```

- Choose a face, a master and the italic.
- Move sliders: they show and edit the selected master's own values.
- Drag points and handles in the glyph view.
- Download the `.otf`.
- Edits are kept in the browser; they can be saved and opened as a file, or
  exported as the face's own files.

[`web/README.md`](../../web/README.md) has the details.

## Measuring against a reference

The benchmark asks how closely the language can represent existing type.
Reference fonts are downloaded for measurement only, into git-ignored
folders:

```bash
python benchmarks/geist_sans/fetch_reference.py
ductus bench examples/sans/font.py --reference benchmarks/geist_sans/reference/Geist-Regular.woff2 --glyphs g --note "what changed"
ductus fit   benchmarks/geist_serif/font.py --glyph o --only-improve
```

- **`bench`** scores each glyph. It aligns ours and the reference on the
  centres of their bounding boxes, then records:
  - exact IoU of the two outlines;
  - Hausdorff and mean outline distance;
  - the change in advance;
  - the overrides used.

  It appends a row to `docs/representability.md` and writes overlays: red
  is ink only in ours, blue ink only in the reference.
- **`fit`** tunes *parameters only*, never overrides, so it measures the
  language rather than hand work. Always pass `--only-improve`, which saves
  only if every glyph improves.
- **Per-glyph refits** for the sans and its masters live in
  `tools/fitting/`; read [the fitting workflow](../fitting.md) first.

Ductus Display and Ductus Notch are designed by eye; never run the fitting
tools on them.

## Proof sheets

Each face has a sheet script, and every iteration of a design log has its
sheet:

```bash
python examples/sans/make_sheet.py NN               # docs/sans/NN.png
python examples/display_serif/make_sheet.py NN      # docs/display_serif/NN.png
python docs/make_proofs.py                          # the proofs in docs/
```

Proofs shape text through the font's GPOS kerning. FreeType alone ignores
the legacy `kern` table of a CFF font, so render with `ductus.proof`.
