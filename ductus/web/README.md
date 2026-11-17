# Ductus in the browser (SPEC M7)

A browser-only editor: Pyodide runs the Ductus compiler in the browser, so
there is nothing to install. It runs in a Web Worker (`worker.js`, which
loads Paper.js and Pyodide and calls `driver.py`), so the page keeps
responding while a preview compiles. Changes made during a compile are
compiled together right after it.

```bash
python web/build.py                 # -> web/_build/: the ductus wheel, examples.zip, driver.py
python -m http.server -d web 8000   # then open http://localhost:8000/
```

- **Booleans.** skia-pathops (overlap removal and cuts) has no Pyodide
  build. When `import pathops` fails, `ductus.compile` uses
  `ductus/_pathops_js.py`, the same small API backed by Paper.js, which
  keeps curves.
- **Packages.** Pyodide supplies NumPy, PyYAML and fontTools. The ductus
  wheel is installed without dependencies.
- **What you can do:**
  - choose a face (Ductus Sans, Ductus Display) and a master (weight, or
    optical size);
  - switch to the italic;
  - move parameter sliders (type in the filter to find any ranged
    parameter). The sliders show and edit the **selected master's own
    values**: at the Bold the stem slider reads 150, not the Regular's 84,
    and a change there is stored for the Bold only. A Regular change still
    carries to the masters wherever they only scale it;
  - **drag construction points** in the glyph view under the preview:
    circles are a stroke's skeleton points, squares the named points of
    the expanded outline (every glyph has those, including the ones built
    from shapes, like the e). Each drag is an override delta, as in
    `overrides.yaml`. An accented letter shows its base's points. The view
    follows the caret in the preview;
  - **click a circle** for that node's stroke controls: width (`dw`),
    direction (`da`), tension (`dt`) and pen angle (`dp`, on turning-pen
    strokes);
  - **drag a triangle** (a primitive handle: join height, notch depth,
    taper length, bowl thin...) along its dashed arm to change that
    parameter for this glyph only (`<glyph>.@<param>: {dv}`);
  - **moves apply to all masters, or to this master only** ("Moves apply
    to"). A master's own moves are exported to `overrides_<value>.yaml`,
    which both faces read for that master (`compile_master` adds a
    setting's `"overrides"`). A move at the default master only is
    exported as an all-master move plus the opposite move at every other
    master, which is exactly that in a variable font;
  - **in italic the glyph view is the italic as built** (slanted, round
    glyphs half rotated). Drags are turned back into the upright move by
    the inverse of the glyph's map (`ductus.italic.slant_matrix`), since
    the italic is derived from the upright;
  - **edits are kept in the browser** (per face; a reload restores them).
    *Save edits…* downloads them as a JSON file; *Open edits* loads one
    back. *Export files* offers the face's files: `overrides.yaml`,
    `overrides_<value>.yaml`, and `params_<value>.json`, the slider values
    per master. Put the default's into `font.py`'s `kit.params`; put another
    master's into its `"params"` (for the sans, `master_bold.json` or
    `master_light.json`);
  - open "Changes" to see the overrides (in `overrides.yaml` format, per
    master) and the slider values per master;
  - **undo / redo** every edit (buttons, ⌘Z / Ctrl+Z, ⇧⌘Z / Ctrl+Y; a
    slider drag is one step; in the preview text the text's own undo
    applies). The history is per face and lasts until the page is reloaded;
  - edit the preview text, which compiles only the glyphs it uses;
  - download the .otf.
- **Offline.** `python web/build.py --pyodide <a Pyodide 0.27.7
  distribution> --paper <paper-core.js>`, then open
  `index.html?pyodide=_build/pyodide/&paper=_build/paper-core.js`.
- **Tests.**
  - `tests/test_pathops_js.py` checks the adapter's glue with a stand-in
    backend. With `DUCTUS_PAPER_JS=<paper-core.js>` it also runs the real
    Paper.js through Node: every glyph of both faces, upright and italic,
    against skia (same contours, area within 0.5%).
  - `tests/test_web_driver.py` checks the page's Python side.
  - `node web/browser_test.mjs` (after `build.py --pyodide … --paper …`)
    opens the page in headless Chromium and checks:
    - each master's sliders show and store that master's own values;
    - drags of a stroke point, an outline point and a handle;
    - a node's width control;
    - a move at the Bold only;
    - a drag in the italic view (stored upright);
    - edits restored after a reload;
    - the export;
    - undo and redo (button and keys; a slider drag is one step);
    - that the page keeps drawing frames (none over 150 ms) while the worker compiles.

    It then switches face and saves screenshots. Each preview takes about 0.5–0.8 s.
- **Where Paper.js needed help** (the guards in `JS_SOURCE`):
  - **Self-union.** Uniting a compound path with an empty path
    mis-resolves overlapping strokes. Instead, each hole goes to the
    smallest outer contour that wholly contains it, and the shapes are
    united pairwise.
  - **Order.** Unite the largest shapes first: small serifs sharing edges
    with a stroke lost area otherwise (display X).
  - **Degenerate pieces.** Drop zero-area pieces: they made a later
    subtract do nothing (display t).
  - **Tangent crossings.** An odd number of intersections means Paper
    missed a tangent crossing. Nudge the second shape by 0.01 u and retry.
