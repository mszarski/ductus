"""Package Ductus for the browser editor (SPEC M7).

    python web/build.py [--pyodide DIR] [--paper FILE]

Writes ``web/_build/`` (git-ignored): the ductus wheel (pure Python), the
example faces as ``examples.zip`` (font.py files with their JSON masters,
kerning and overrides), ``driver.py`` and ``manifest.json``. Then serve the
``web/`` folder over HTTP (``python -m http.server -d web``) and open
``index.html``. Pyodide and Paper.js load from their CDNs unless the page is
given ``?pyodide=<base url>&paper=<url>``; ``--pyodide`` / ``--paper``
copy local copies into ``_build/`` for offline use (then open
``index.html?pyodide=_build/pyodide/&paper=_build/paper-core.js``).
"""
import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "_build"
FACES = ["examples/sans", "examples/display_serif"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pyodide", type=Path, help="a local Pyodide distribution to copy (offline use)")
    ap.add_argument("--paper", type=Path, help="a local paper-core.js to copy (offline use)")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("ductus-*.whl"):
        old.unlink()
    subprocess.run([sys.executable, "-m", "pip", "wheel", str(ROOT), "--no-deps", "-q", "-w", str(OUT)], check=True)
    wheel = sorted(OUT.glob("ductus-*.whl"))[-1].name
    with zipfile.ZipFile(OUT / "examples.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for face in FACES:
            for f in sorted((ROOT / face).iterdir()):
                if f.suffix in (".py", ".json", ".yaml") and not f.name.startswith("make_"):
                    z.write(f, Path(face).name + "/" + f.name)
    shutil.copy(HERE / "driver.py", OUT / "driver.py")
    (OUT / "manifest.json").write_text(json.dumps({"wheel": wheel}))
    if a.pyodide:
        shutil.copytree(a.pyodide, OUT / "pyodide", dirs_exist_ok=True)
    if a.paper:
        shutil.copy(a.paper, OUT / "paper-core.js")
    print(f"wrote {OUT}: {wheel}, examples.zip, driver.py, manifest.json")


if __name__ == "__main__":
    main()
