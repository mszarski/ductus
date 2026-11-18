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
    for g in "nkvdMK":             # (A and G are skipped: see font.traps)
        assert abs(sum(c.area() for c in trapped.glyphs[g].contours)) < \
            abs(sum(c.area() for c in plain.glyphs[g].contours)) - 50, g
        assert trapped.glyphs[g].advance == plain.glyphs[g].advance
    for n, g in trapped.glyphs.items():
        assert not [x for x in check_self_intersections(g) + check_direction(g) if x.level == "error"], n
    # skipped marks keep their outline (a comma's dot-to-tail joint is no crotch)
    assert trapped.glyphs["comma"].to_json()["svg"] == plain.glyphs["comma"].to_json()["svg"]
    assert trapped.glyphs["G"].to_json()["svg"] == plain.glyphs["G"].to_json()["svg"]


def test_notch_signatures(notch):
    cf = compile_font(notch, glyphs=["g", "y", "j", "k", "K", "R", "e", "t"])
    # descenders reach the descender; the y's tail runs straight (one straight stroke: two segments' worth of
    # on-curve points at most)
    for g in "gy":
        assert cf.glyphs[g].bounds[1] < -170
    tail = [s for s in cf.glyphs["y"].to_json()["skeleton"] if s["name"].endswith("tail")][0]
    assert len(tail["nodes"]) == 2
    # the branched k: its leg starts well off the stem
    leg = [s for s in cf.glyphs["k"].to_json()["skeleton"] if s["name"].endswith("leg")][0]
    assert leg["nodes"][0]["x"] > 100


# ---- tidy (ductus.tidy): the small leftovers of overlapping strokes ----------------

from ductus.tidy import tidy_contour


def test_tidy_collapses_a_small_step_and_keeps_real_corners():
    # a rectangle whose right side has a 6-unit step halfway up (a stroke ending a little off its neighbour)
    c = _poly([(0, 0), (200, 0), (200, 100), (206, 100), (206, 300), (0, 300)])
    t = tidy_contour(c, 12, 150)
    assert len(t.pts) == 5 and [203, 100] in t.pts          # the step's two corners became one
    big = _poly([(0, 0), (200, 0), (200, 100), (240, 100), (240, 300), (0, 300)])
    assert len(tidy_contour(big, 12, 150).pts) == 6          # a 40-unit step is design, not a leftover


def test_tidy_removes_a_needle_spike():
    c = _poly([(0, 0), (200, 0), (200, 150), (230, 152), (200, 154), (200, 300), (0, 300)])
    t = tidy_contour(c, 12, 150)
    assert [230, 152] not in t.pts


def test_notch_outlines_are_tidy_and_traps_only_at_real_crotches(notch):
    cf = compile_font(notch)
    # tidying is idempotent on the compiled outlines (nothing left to collapse)
    for n, g in cf.glyphs.items():
        for c in (g.untrapped or g.contours):
            assert tidy_contour(c, 16, 150).pts == [[float(round(x)), float(round(y))] for x, y in c.pts], n
    # the f is skipped (its hook-to-bar corner is no crotch between two strokes)
    f_ = cf.glyphs["f"]
    assert f_.untrapped is None or [c.pts for c in f_.contours] == [c.pts for c in f_.untrapped]
