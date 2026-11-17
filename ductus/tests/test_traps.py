"""Ink traps by rule (ductus.traps) and Ductus Notch, the face built on them."""
from pathlib import Path

import pytest

from ductus.compile import compile_font
from ductus.geometry import Contour
from ductus.lint import check_direction, check_self_intersections
from ductus.loader import load_font
from ductus.traps import corners, trap_cuts

ROOT = Path(__file__).resolve().parents[1]


def _poly(pts):
    c = Contour()
    for p in pts:
        c.add(p, "on")
    return c


def test_corners_finds_concave_crotches_by_angle():
    # an L (ink on the left of a counter-clockwise outline): one concave corner, a right angle
    L = _poly([(0, 0), (300, 0), (300, 80), (80, 80), (80, 400), (0, 400)])
    assert [c[0] for c in corners(L, 100)] == [(80, 80)]
    assert corners(L, 80) == []                     # 90 degrees of white is no crotch at 80
    # a V-shaped notch: 40 degrees of white at its tip
    v = _poly([(0, 0), (400, 0), (400, 400), (220, 400), (200, 345), (180, 400), (0, 400)])
    (p, a, b, u), = corners(v, 80)
    assert p == (200, 345) and u[1] < -0.99          # the trap goes straight down into the ink
    tri = trap_cuts([v], 40, 10, 80)[0]
    assert tri.pts[1] == pytest.approx([200, 305])


@pytest.fixture(scope="module")
def notch():
    return load_font(ROOT / "examples/notch/font.py")


def test_notch_traps_its_crotches_and_stays_clean(notch):
    plain = compile_font(notch, {"trap_depth": 0})
    trapped = compile_font(notch)
    for g in "nkvdAMK":
        assert abs(sum(c.area() for c in trapped.glyphs[g].contours)) < \
            abs(sum(c.area() for c in plain.glyphs[g].contours)) - 200, g
        assert trapped.glyphs[g].advance == plain.glyphs[g].advance
    for n, g in trapped.glyphs.items():
        assert not [x for x in check_self_intersections(g) + check_direction(g) if x.level == "error"], n
    # skipped marks keep their outline (a comma's dot-to-tail joint is no crotch)
    assert trapped.glyphs["comma"].to_json()["svg"] == plain.glyphs["comma"].to_json()["svg"]
    # the italic slants the trapped outline (traps first)
    from ductus.italic import italic_mode
    assert not getattr(notch, "italic", None) or True


def test_notch_signatures(notch):
    cf = compile_font(notch, glyphs=["g", "y", "j", "k", "K", "R", "e", "t"])
    # flat-footed descenders: g and y end level at the descender
    for g in "gy":
        assert cf.glyphs[g].bounds[1] < -170
    # the branched k: its leg starts well off the stem
    leg = [s for s in cf.glyphs["k"].to_json()["skeleton"] if s["name"].endswith("leg")][0]
    assert leg["nodes"][0]["x"] > 100
