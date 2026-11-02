"""Variable fonts (SPEC M3): exact point-compatibilisation of master outlines,
and the weight axis built from the sans's masters."""
from pathlib import Path

import pytest

from ductus.compat import compatible
from ductus.terminals import poly

ROOT = Path(__file__).resolve().parents[1]


def _area(cs):
    return sum(c.area() for c in cs)


def test_compatible_unifies_different_segmentations_without_changing_shape():
    # the same kind of shape, segmented differently and started at another corner
    a = poly([(0, 0), (100, 0), (100, 100), (0, 100)])
    b = poly([(120, 0), (120, 60), (120, 130), (0, 130), (0, 0), (60, 0)])
    r = compatible([[a], [b]])
    assert r is not None
    assert r[0][0].signature() == r[1][0].signature()
    assert abs(_area(r[0]) - _area([a])) < 1e-6 and abs(_area(r[1]) - _area([b])) < 1e-6
    # each master starts at the corner nearest the reference's start (bottom left)
    assert r[0][0].pts[0] == [0.0, 0.0] and r[1][0].pts[0] == [0.0, 0.0]


def test_compatible_refuses_a_change_of_topology():
    a = poly([(0, 0), (100, 0), (100, 100), (0, 100)])
    hole = poly([(30, 30), (30, 70), (70, 70), (70, 30)])
    assert compatible([[a, hole], [a]]) is None


def test_sans_weight_axis_builds_with_every_glyph_varying(tmp_path):
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.pens.boundsPen import BoundsPen
    from ductus.compile import compile_font
    from ductus.emit import validate_otf
    from ductus.loader import load_font
    from ductus.variable import build_variable
    font = load_font(ROOT / "examples/sans/font.py")
    path, held = build_variable(font, tmp_path / "vf.otf")
    assert held == {}
    assert not validate_otf(path)
    vf = TTFont(path)
    ax = vf["fvar"].axes[0]
    assert (ax.axisTag, ax.minValue, ax.defaultValue, ax.maxValue) == ("wght", 300, 400, 700)
    # the default instance is the regular
    reg = compile_font(font)
    inst = instantiateVariableFont(TTFont(path), {"wght": 400})
    gs = inst.getGlyphSet()
    for g in ("n", "a", "g", "R", "ampersand"):
        p = BoundsPen(gs); gs[g].draw(p)
        assert all(abs(x - y) <= 1 for x, y in zip(p.bounds, reg.glyphs[g].bounds)), g
    # and the bold one is heavier
    bold = instantiateVariableFont(TTFont(path), {"wght": 700})
    from fontTools.pens.areaPen import AreaPen
    def ink(f, g):
        ap = AreaPen(f.getGlyphSet()); f.getGlyphSet()[g].draw(ap); return abs(ap.value)
    assert ink(bold, "n") > 1.3 * ink(inst, "n")


def test_variable_kerning_is_each_masters_own(tmp_path):
    # font.variable["kerning"] gives a master its own pairs; the variable font
    # interpolates them (a pair only one master has is 0 in the others)
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from ductus.loader import load_font
    from ductus.proof import gpos_kerning
    from ductus.variable import build_variable
    font = load_font(ROOT / "examples/sans/font.py")
    reg = dict(font.kerning)
    pair = next(p for p, v in sorted(reg.items()) if v <= -20)
    names = sorted({g for pr in reg for g in pr})
    new = next((a, b) for a in names for b in names if (a, b) not in reg)    # a pair only the bold has
    font.variable = dict(font.variable, kerning={700: {pair: reg[pair] - 40, new: -12}, 300: {}})
    path, _ = build_variable(font, tmp_path / "vf.otf")
    k = {}
    for w in (300, 400, 550, 700):
        p = tmp_path / f"i{w}.otf"
        instantiateVariableFont(TTFont(path), {"wght": w}).save(str(p))
        k[w] = gpos_kerning(p)
    assert k[400].get(pair) == reg[pair]
    assert k[700].get(pair) == reg[pair] - 40
    assert k[700].get(new) == -12 and not k[400].get(new)
    assert not k[300].get(pair)
    assert reg[pair] - 40 < k[550][pair] < reg[pair]
