# Ductus in the browser (SPEC M7)

A browser-only editor: Pyodide runs the Ductus compiler in the page, so
there is nothing to install.

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
    parameter);
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
    opens the page in headless Chromium. It compiles six states (sans at
    400 / 700 / 700 italic, display at 72 / 9 / stem 120) and saves
    screenshots. Each preview takes about 0.5–0.75 s.
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
