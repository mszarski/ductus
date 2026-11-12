"""The Python side of the browser editor (SPEC M7), run inside Pyodide.

``web/index.html`` unpacks the example faces into ``/home/pyodide/examples``
and installs the ductus wheel; this module compiles a face (only the glyphs
the preview text needs) and returns the .otf bytes for the page to load as a
web font. Booleans go through Paper.js (``ductus._pathops_js``), as
skia-pathops has no Pyodide build.

The page's **state** is ``{axis value: {param: value}}``: the values the user
set at each master. The default master's values are the font's parameters;
another master's values replace that master's own designed ones (they are
merged into its setting's ``"params"``), so its sliders show and edit what
that master really uses. **Overrides** are ``{point name: {dx, dy}}`` deltas
from dragging construction points (``stage: outline`` for a point of the expanded
outline, else a skeleton node), added to the face's ``overrides.yaml``.
"""
import json
import time
from pathlib import Path

from ductus.compile import compile_font
from ductus.emit import build_otf
from ductus.italic import italic_mode
from ductus.loader import load_font
from ductus.overrides import Override, load_overrides

EXAMPLES = Path("/home/pyodide/examples")
FACES = {"sans": EXAMPLES / "sans/font.py", "display": EXAMPLES / "display_serif/font.py"}
_fonts = {}
_cache = {}


def _font(face):
    if face not in _fonts:
        _fonts[face] = load_font(FACES[face])
    return _fonts[face]


def _state(state_json) -> dict:
    """{axis value (float): {param: float}} from the page's JSON (keys are strings there)."""
    return {float(k): {p: float(v) for p, v in d.items()} for k, d in json.loads(state_json or "{}").items()}


def _overrides(face, overrides_json) -> dict:
    ovs = dict(load_overrides(FACES[face].with_name("overrides.yaml")))
    for name, d in json.loads(overrides_json or "{}").items():
        base = ovs.get(name)
        dx = float(d.get("dx", 0)) + (base.dx if base else 0.0)
        dy = float(d.get("dy", 0)) + (base.dy if base else 0.0)
        ovs[name] = Override(name, dx=dx, dy=dy, stage=d.get("stage", "skeleton")) if base is None else \
            Override(name, dx=dx, dy=dy, stage=base.stage, dw=base.dw, da=base.da, dt=base.dt, dv=base.dv, dp=base.dp)
    return ovs


def _default_params(face, state) -> dict:
    """The default master's evaluated parameters with its slider values applied."""
    f = _font(face)
    spec = getattr(f, "variable", None)
    values = state.get(float(spec["default"]), {}) if spec else next(iter(state.values()), {})
    key = (face, json.dumps(values, sort_keys=True))
    if key not in _cache:
        _cache.clear()
        _cache[key] = (values, compile_font(f, values, glyphs=[]).params)
    return _cache[key]


def _setting(spec, state, master):
    s = spec["masters"][master]
    s = dict(s) if isinstance(s, dict) else {"k": s}
    s["params"] = {**s.get("params", {}), **state.get(float(master), {})}
    return s


def _is_master(spec, master) -> bool:
    return bool(spec) and master is not None and master != spec["default"] and master in spec["masters"]


def describe(face: str) -> str:
    """JSON: the family, its axis and masters, and whether it has an italic."""
    f = _font(face)
    spec = getattr(f, "variable", None) or {}
    return json.dumps({
        "family": f.family,
        "axis": spec.get("tag"),
        "masters": sorted([spec["default"], *spec["masters"]]) if spec else [],
        "default": spec.get("default"),
        "italic": bool(getattr(f, "italic", None)),
    })


def master_values(face: str, state_json: str, master) -> str:
    """JSON {param: [value, [lo, hi]]}: every ranged parameter's effective value at
    ``master`` (its own designed or weight-scaled value, or the user's), with a slider
    range widened to hold it (a Bold's stems lie beyond the Regular's ranges)."""
    f = _font(face)
    state = _state(state_json)
    spec = getattr(f, "variable", None)
    _, params = _default_params(face, state)
    eff = dict(params)
    if _is_master(spec, master):
        eff.update({k: float(v) for k, v in spec["params"](params, _setting(spec, state, master)).items()
                    if k in params})
    out = {}
    for n, p in f.params.items():
        if not p.range or not isinstance(p.default, (int, float)):
            continue
        v = float(eff[n])
        lo, hi = p.range
        pad = (hi - lo) * 0.2
        out[n] = [v, [min(lo, v - pad) if v < lo else lo, max(hi, v + pad) if v > hi else hi]]
    return json.dumps(out)


def _names_for(f, text: str):
    chars = set(text)
    names = {g.name for g in f.glyphs.values() if g.unicode is not None and chr(g.unicode) in chars}
    names |= {n for n, c in getattr(f, "composites", {}).items()
              if c.get("unicode") is not None and chr(c["unicode"]) in chars}
    names |= {lg for lg, comps in getattr(f, "ligatures", {}).items() if set(comps) <= names}
    if " " in chars and "space" in f.glyphs:
        names.add("space")
    return sorted(names)


def _compile(face, state, master, names, overrides):
    f = _font(face)
    spec = getattr(f, "variable", None)
    values, params = _default_params(face, state)
    if _is_master(spec, master):
        from ductus.variable import compile_master
        return compile_master(f, params, _setting(spec, state, master), overrides, glyphs=names)
    return compile_font(f, values, overrides, glyphs=names)


def build(face: str, state_json: str, text: str, italic: bool, master, overrides_json: str = "{}"):
    """(otf bytes, compile ms, glyph count) for ``text`` set in the face at axis value
    ``master`` with the page's state and overrides, upright or italic."""
    f = _font(face)
    t0 = time.perf_counter()
    with italic_mode(bool(italic)):
        cf = _compile(face, _state(state_json), master, _names_for(f, text), _overrides(face, overrides_json))
    ms = (time.perf_counter() - t0) * 1000
    out = Path("/tmp/preview.otf")
    build_otf(cf, out)
    return out.read_bytes(), ms, len(cf.glyphs)


def glyph(face: str, state_json: str, char: str, master, overrides_json: str = "{}") -> str:
    """JSON for the glyph view: the upright glyph for ``char`` at ``master`` -- its outline
    (SVG path, y up), skeleton strokes with their named nodes, the named points of the
    expanded outline, advance and the metrics. Dragging a node by (dx, dy) font units is
    the override ``{name: {dx, dy}}``; an outline point's also carries ``stage: outline``."""
    f = _font(face)
    names = _names_for(f, char)
    if not names:
        return json.dumps({"error": f"no glyph for {char!r}"})
    with italic_mode(False):
        cf = _compile(face, _state(state_json), master, names, _overrides(face, overrides_json))
    # the character's own glyph (a composite brings its base along)
    want = [n for n, g in cf.glyphs.items() if g.unicode is not None and chr(g.unicode) == char]
    g = cf.glyphs[want[0] if want else names[0]]
    j = g.to_json()
    # an accented letter keeps no construction of its own: show its base's (it sits in the same place)
    base = getattr(f, "composites", {}).get(g.name, {}).get("base")
    src = j
    if base:
        with italic_mode(False):
            src = _compile(face, _state(state_json), master, [base], _overrides(face, overrides_json)).glyphs[base].to_json()
    return json.dumps({
        "name": g.name, "advance": g.advance, "svg": j["svg"], "bounds": g.bounds, "points_of": base or g.name,
        "skeleton": src["skeleton"], "outline_points": src["outline_points"], "metrics": cf.metrics,
    })
