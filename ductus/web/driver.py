"""The Python side of the browser editor (SPEC M7), run inside Pyodide.

``web/app.js`` unpacks the example faces into ``/home/pyodide/examples`` and
installs the ductus wheel; this module compiles a face (only the glyphs the
preview text needs) and returns the .otf bytes for the page to load as a
web font. Booleans go through Paper.js (``ductus._pathops_js``), as
skia-pathops has no Pyodide build.
"""
import json
import time
from pathlib import Path

from ductus.compile import compile_font
from ductus.emit import build_otf
from ductus.italic import italic_mode
from ductus.loader import load_font

EXAMPLES = Path("/home/pyodide/examples")
FACES = {"sans": EXAMPLES / "sans/font.py", "display": EXAMPLES / "display_serif/font.py"}
_fonts = {}
_defaults = {}


def _font(face):
    if face not in _fonts:
        _fonts[face] = load_font(FACES[face])
    return _fonts[face]


def describe(face: str) -> str:
    """JSON: the face's ranged parameters (sliders), its masters and whether it has an italic."""
    f = _font(face)
    spec = getattr(f, "variable", None) or {}
    params = {n: [float(p.default), list(p.range)] for n, p in f.params.items()
              if p.range and isinstance(p.default, (int, float))}
    return json.dumps({
        "family": f.family,
        "params": params,
        "axis": spec.get("tag"),
        "masters": sorted([spec["default"], *spec["masters"]]) if spec else [],
        "default": spec.get("default"),
        "italic": bool(getattr(f, "italic", None)),
    })


def _names_for(f, text: str):
    chars = set(text)
    names = {g.name for g in f.glyphs.values() if g.unicode is not None and chr(g.unicode) in chars}
    names |= {n for n, c in getattr(f, "composites", {}).items()
              if c.get("unicode") is not None and chr(c["unicode"]) in chars}
    names |= {lg for lg, comps in getattr(f, "ligatures", {}).items() if set(comps) <= names}
    if " " in chars and "space" in f.glyphs:
        names.add("space")
    return sorted(names)


def build(face: str, values_json: str, text: str, italic: bool, master) -> tuple[bytes, float, int]:
    """(otf bytes, compile ms, glyph count) for ``text`` set in the face with
    the slider ``values``, at axis value ``master`` (the default, or one of
    font.variable's masters), upright or italic."""
    f = _font(face)
    values = {k: float(v) for k, v in json.loads(values_json).items()}
    names = _names_for(f, text)
    spec = getattr(f, "variable", None)
    t0 = time.perf_counter()
    with italic_mode(bool(italic)):
        if spec and master is not None and master != spec["default"] and master in spec["masters"]:
            from ductus.variable import compile_master
            key = (face, json.dumps(values, sort_keys=True))
            if key not in _defaults:
                _defaults[key] = compile_font(f, values, glyphs=[]).params
            cf = compile_master(f, _defaults[key], spec["masters"][master], glyphs=names)
        else:
            cf = compile_font(f, values, glyphs=names)
    ms = (time.perf_counter() - t0) * 1000
    out = Path("/tmp/preview.otf")
    build_otf(cf, out)
    return out.read_bytes(), ms, len(cf.glyphs)
