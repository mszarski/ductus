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
that master really uses.

**Overrides** are the page's hand adjustments, ``{"all": {name: deltas},
"masters": {axis value: {name: deltas}}}`` in overrides.yaml's delta format
(dx dy from dragging points, ``stage: outline`` for a point of the expanded
outline; dw da dt dp at a skeleton node; dv on ``<glyph>.@<param>`` from a
primitive handle). ``all`` is added to the face's ``overrides.yaml``; a
master's own are added at that master only (on top of its
``overrides_<value>.yaml``). A flat ``{name: deltas}`` counts as ``all``.
:func:`export` turns them into those files.
"""
import json
import time
from pathlib import Path

from ductus.compile import compile_font
from ductus.emit import build_otf
from ductus.italic import apply, glyph_matrix, invert_linear, italic_mode
from ductus.loader import load_font
from ductus.overrides import DELTAS, Override, dump_overrides, load_overrides, merge_overrides, parse_overrides

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


def _page_overrides(overrides_json):
    """(all, {axis value: own}) from the page's JSON, each {name: Override}."""
    data = json.loads(overrides_json or "{}")
    if "all" not in data and "masters" not in data:
        data = {"all": data}
    clean = lambda d: {n: {k: v for k, v in o.items() if k in DELTAS or k == "stage"} for n, o in (d or {}).items()}
    return (parse_overrides(clean(data.get("all"))),
            {float(m): parse_overrides(clean(d)) for m, d in (data.get("masters") or {}).items()})


def _overrides(face, overrides_json, master=None) -> dict:
    """The overrides a compile at ``master`` starts from: overrides.yaml + the page's
    ``all``, and at the default master its own too (another master's own go in its
    setting, see :func:`_setting`)."""
    allv, own = _page_overrides(overrides_json)
    ovs = merge_overrides(load_overrides(FACES[face].with_name("overrides.yaml")), allv)
    spec = getattr(_font(face), "variable", None)
    if master is not None and not _is_master(spec, master):
        ovs = merge_overrides(ovs, own.get(float(master), {}))
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


def _setting(spec, state, master, own=None):
    s = spec["masters"][master]
    s = dict(s) if isinstance(s, dict) else {"k": s}
    s["params"] = {**s.get("params", {}), **state.get(float(master), {})}
    if own:
        s["overrides"] = merge_overrides(s.get("overrides") or {}, own)
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


def _compile(face, state, master, names, overrides_json):
    f = _font(face)
    spec = getattr(f, "variable", None)
    values, params = _default_params(face, state)
    ovs = _overrides(face, overrides_json, master)
    if _is_master(spec, master):
        from ductus.variable import compile_master
        own = _page_overrides(overrides_json)[1].get(float(master))
        return compile_master(f, params, _setting(spec, state, master, own), ovs, glyphs=names)
    return compile_font(f, values, ovs, glyphs=names)


def build(face: str, state_json: str, text: str, italic: bool, master, overrides_json: str = "{}"):
    """(otf bytes, compile ms, glyph count) for ``text`` set in the face at axis value
    ``master`` with the page's state and overrides, upright or italic."""
    f = _font(face)
    t0 = time.perf_counter()
    with italic_mode(bool(italic)):
        cf = _compile(face, _state(state_json), master, _names_for(f, text), overrides_json)
    ms = (time.perf_counter() - t0) * 1000
    out = Path("/tmp/preview.otf")
    build_otf(cf, out)
    return out.read_bytes(), ms, len(cf.glyphs)


def glyph(face: str, state_json: str, char: str, master, overrides_json: str = "{}", italic: bool = False) -> str:
    """JSON for the glyph view: the glyph for ``char`` at ``master`` -- its outline (SVG
    path, y up), skeleton strokes with their named nodes (direction, width, tension,
    pen angle), the named points of the expanded outline, the primitive handles,
    advance and the metrics. Dragging a node by (dx, dy) font units is the override
    ``{name: {dx, dy}}``; an outline point's also carries ``stage: outline``; a
    handle's drag projected on its axis, over ``per_unit``, is ``<glyph>.@<param>: {dv}``.

    With ``italic`` (and a face that has one) everything is shown slanted, as the
    italic is built; ``matrix`` is the map applied and ``inverse`` its linear part's
    inverse, which turns a move in the view back into the upright move to store."""
    f = _font(face)
    names = _names_for(f, char)
    if not names:
        return json.dumps({"error": f"no glyph for {char!r}"})
    state = _state(state_json)
    with italic_mode(False):
        cf = _compile(face, state, master, names, overrides_json)
    # the character's own glyph (a composite brings its base along)
    want = [n for n, g in cf.glyphs.items() if g.unicode is not None and chr(g.unicode) == char]
    g = cf.glyphs[want[0] if want else names[0]]
    j = g.to_json()
    # an accented letter keeps no construction of its own: show its base's (it sits in the same place)
    base = getattr(f, "composites", {}).get(g.name, {}).get("base")
    src = j
    if base:
        with italic_mode(False):
            src = _compile(face, state, master, [base], overrides_json).glyphs[base].to_json()
    skeleton, points, handles, svg = src["skeleton"], src["outline_points"], src["handles"], j["svg"]
    m = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    if italic and getattr(f, "italic", None):
        m = glyph_matrix(f, g.name, g, cf.metrics)
        from ductus.geometry import svg_path
        from ductus.italic import _transform
        svg = svg_path(_transform(g.contours, lambda x, y: apply(m, x, y)))
        skeleton = [{**st, "nodes": [{**n, **dict(zip("xy", apply(m, n["x"], n["y"])))} for n in st["nodes"]],
                     "segments": [[list(apply(m, *q)) for q in seg] for seg in st.get("segments", [])]}
                    for st in skeleton]
        points = {k: list(apply(m, *p)) for k, p in points.items()}
        handles = [{**h, "uax": h["ax"], "uay": h["ay"], **dict(zip("xy", apply(m, h["x"], h["y"]))),
                    **dict(zip(("ax", "ay"), _unit(m[0] * h["ax"] + m[2] * h["ay"], m[1] * h["ax"] + m[3] * h["ay"])))}
                   for h in handles]
    return json.dumps({
        "name": g.name, "advance": g.advance, "svg": svg, "bounds": g.bounds, "points_of": base or g.name,
        "skeleton": skeleton, "outline_points": points, "handles": handles, "metrics": cf.metrics,
        "italic_angle": float(f.italic.get("angle", 10)) if italic and getattr(f, "italic", None) else 0.0,
        "matrix": m, "inverse": invert_linear(m),
    })


def _unit(x, y):
    n = (x * x + y * y) ** 0.5 or 1.0
    return x / n, y / n


def export(face: str, state_json: str, overrides_json: str) -> str:
    """JSON {file name: text}: the page's edits as files for the face's folder.

    * ``overrides.yaml`` -- the face's own plus the page's ``all`` moves;
    * ``overrides_<value>.yaml`` -- a master's own moves (with that file's existing ones);
    * ``params_<value>.json`` -- the slider values set at a master (the default's go
      into font.py's ``kit.params``; another's into its ``"params"``, for the sans
      master_bold.json / master_light.json).

    A move made at the default master only is written as an ``all`` move with the
    opposite move at every other master, which is exactly that in a variable font."""
    f = _font(face)
    spec = getattr(f, "variable", None)
    folder = FACES[face].parent
    allv, own = _page_overrides(overrides_json)
    default = float(spec["default"]) if spec else None
    others = [float(m) for m in spec["masters"]] if spec else []
    d_own = own.get(default, {}) if spec else {}
    if not spec:
        allv = merge_overrides(allv, next(iter(own.values()), {}))
    negated = {n: Override(n, stage=o.stage, **{k: -getattr(o, k) for k in DELTAS}) for n, o in d_own.items()}
    out = {}
    if allv or d_own:
        out["overrides.yaml"] = dump_overrides(merge_overrides(merge_overrides(
            load_overrides(folder / "overrides.yaml"), allv), d_own))
    for m in others:
        mine = merge_overrides(own.get(m, {}), negated)
        if mine:
            tag = f"{m:g}"
            out[f"overrides_{tag}.yaml"] = dump_overrides(merge_overrides(
                load_overrides(folder / f"overrides_{tag}.yaml"), mine))
    for m, values in _state(state_json).items():
        if values:
            out[f"params_{m:g}.json"] = json.dumps({k: round(v, 3) for k, v in sorted(values.items())}, indent=1) + "\n"
    return json.dumps(out)
