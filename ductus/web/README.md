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
- **Tests (CPython).**
  - `tests/test_pathops_js.py` checks the adapter's glue with a stand-in
    backend.
  - `tests/test_web_driver.py` checks the page's Python side.

  Paper.js itself is not exercised by the test suite.
