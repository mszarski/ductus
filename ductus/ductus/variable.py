"""Variable fonts: interpolate parameter-setting masters along an axis.

A font module declares its axis::

    font.variable = {
        "tag": "wght", "name": "Weight", "default": 400,
        "masters": {300: 0.7, 700: 1.45},         # axis value -> master setting
        "params": kit.weight_master,               # (default params, setting) -> overrides
        "instances": {"Light": 300, "Regular": 400, "Bold": 700},
    }

Each master is compiled with the overrides ``params(default.params, setting)``.
Raw strokes are point-compatible by construction, but overlap removal and
cuts can re-segment the merged outline differently at another weight, so
every glyph's masters are unified by :func:`ductus.compat.compatible` (exact:
shapes are unchanged, only the point structure is matched). The masters are
written as CFF fonts and merged by ``fontTools.varLib`` into a CFF2 variable
font. Kerning is the default master's, static, for now.
"""
from __future__ import annotations

import dataclasses
import tempfile
from pathlib import Path

from .compat import compatible
from . import compat
from .compile import CompiledFont, compile_font
from .emit import build_otf, ps_name
from .parts import DuctusError


def compile_master(font, default_params, setting, overrides=None, glyphs=None):
    """One master: the font compiled with ``font.variable["params"](default
    params, setting)``; a dict setting may also carry ``"spacing"``, per-glyph
    (dl, dr) side-bearing deltas added to ``font.spacing`` for this master."""
    spec = font.variable
    extra = setting.get("spacing", {}) if isinstance(setting, dict) else {}
    saved = dict(getattr(font, "spacing", {}))
    try:
        if extra:
            sp = font.spacing
            for g, (dl, dr) in extra.items():
                l0, r0 = sp.get(g, (0, 0))
                sp[g] = (l0 + dl, r0 + dr)
        return compile_font(font, spec["params"](default_params, setting), overrides, glyphs=glyphs)
    finally:
        font.spacing.clear()
        font.spacing.update(saved)


def compile_masters(font, overrides=None):
    """[(axis value, CompiledFont)] with the default first, every glyph's
    outlines made point-compatible across them; and the glyphs that could
    not be (with the reason)."""
    spec = font.variable
    default = compile_font(font, overrides=overrides)
    masters = [(spec["default"], default)]
    for loc, setting in sorted(spec["masters"].items()):
        masters.append((loc, compile_master(font, default.params, setting, overrides)))
    failed = {}
    unified: dict[str, list] = {}
    for name in default.glyphs:
        r = compatible([cf.glyphs[name].contours for _, cf in masters])
        if r is None:
            failed[name] = compat.LAST_FAIL
            r = [default.glyphs[name].contours for _ in masters]      # held static
        unified[name] = r
    out = []
    for k, (loc, cf) in enumerate(masters):
        glyphs = {n: dataclasses.replace(g, contours=unified[n][k]) for n, g in cf.glyphs.items()}
        out.append((loc, dataclasses.replace(cf, glyphs=glyphs)))
    return out, failed


def build_variable(font, path, overrides=None) -> tuple[Path, dict]:
    """Write the variable font to ``path``; returns (path, glyphs held static)."""
    from fontTools import varLib
    from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor
    from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
    from fontTools.ttLib import TTFont
    spec = getattr(font, "variable", None)
    if not spec:
        raise DuctusError("the font declares no variable axis (font.variable)")
    masters, failed = compile_masters(font, overrides)
    default = masters[0][1]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        ds = DesignSpaceDocument()
        locs = [loc for loc, _ in masters]
        ax = AxisDescriptor()
        ax.tag, ax.name = spec["tag"], spec.get("name", spec["tag"])
        ax.minimum, ax.default, ax.maximum = min(locs), spec["default"], max(locs)
        ds.addAxis(ax)
        for loc, cf in masters:
            cf = dataclasses.replace(cf, kerning={}, ligatures=cf.ligatures)
            p = Path(tmp) / f"master_{loc}.otf"
            build_otf(cf, p, optimize=False)
            src = SourceDescriptor()
            src.path, src.name = str(p), f"master.{loc}"
            src.location = {ax.name: loc}
            ds.addSource(src)
        for iname, loc in spec.get("instances", {}).items():
            inst = InstanceDescriptor()
            inst.styleName, inst.familyName = iname, font.family
            inst.location = {ax.name: loc}
            inst.postScriptFontName = f"{ps_name(default).split('-')[0]}-{iname.replace(' ', '')}"
            ds.addInstance(inst)
        vf, _, _ = varLib.build(ds)
    if default.kerning:
        fea = "feature kern {\n" + "".join(f"  pos {a} {b} {v};\n" for (a, b), v in sorted(default.kerning.items())) \
              + "} kern;\n"
        addOpenTypeFeaturesFromString(vf, fea)
    vf.save(str(path))
    return path, failed
