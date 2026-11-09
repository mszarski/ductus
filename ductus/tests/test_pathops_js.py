"""The Paper.js boolean adapter (M7: the compiler in the browser).

Paper.js itself only runs in a browser (or Node); here a stand-in backend
does the boolean work with skia-pathops but answers in Paper's format
(segments with relative handles, contours in arbitrary direction), so the
adapter's glue -- SVG out, segments in, quadratics, re-orientation, nesting
-- is checked against the real compiler on real glyphs.
"""
from pathlib import Path

import pathops
import pytest
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path

from ductus import _pathops_js as pj
from ductus import compile as comp
from ductus.compile import compile_font
from ductus.loader import load_font

ROOT = Path(__file__).resolve().parents[1]


def _skia(d: str) -> pathops.Path:
    p = pathops.Path()
    if d:
        parse_path(d, p.getPen())
    return p


def _paper_segments(path: pathops.Path, flip_every_other=True):
    """skia's result in Paper's format: per contour, segments [x, y, in_dx, in_dy, out_dx, out_dy]."""
    rp = RecordingPen()
    path.draw(rp)
    contours, segs = [], None
    for opname, args in rp.value:
        if opname == "moveTo":
            segs = [[*args[0], 0, 0, 0, 0]]
        elif opname == "lineTo":
            segs.append([*args[0], 0, 0, 0, 0])
        elif opname in ("curveTo", "qCurveTo"):
            if opname == "qCurveTo":
                (q, p), p0 = args, segs[-1][:2]
                c1 = (p0[0] + 2 / 3 * (q[0] - p0[0]), p0[1] + 2 / 3 * (q[1] - p0[1]))
                c2 = (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1]))
            else:
                c1, c2, p = args
            prev = segs[-1]
            prev[4], prev[5] = c1[0] - prev[0], c1[1] - prev[1]
            segs.append([p[0], p[1], c2[0] - p[0], c2[1] - p[1], 0, 0])
        elif opname == "closePath":
            if len(segs) > 1 and abs(segs[-1][0] - segs[0][0]) < 1e-9 and abs(segs[-1][1] - segs[0][1]) < 1e-9:
                segs[0][2], segs[0][3] = segs[-1][2], segs[-1][3]
                segs.pop()
            contours.append(segs)
    if flip_every_other:          # Paper may hand contours back in either direction
        for i in range(1, len(contours), 2):
            c = contours[i]
            contours[i] = [[s[0], s[1], s[4], s[5], s[2], s[3]] for s in reversed(c)]
    return contours


def _fake_paper(da, db, op):
    a = _skia(da)
    if op == "simplify":
        a.simplify(fix_winding=True)
        return _paper_segments(a)
    kind = {"union": pathops.PathOp.UNION, "difference": pathops.PathOp.DIFFERENCE,
            "intersection": pathops.PathOp.INTERSECTION, "xor": pathops.PathOp.XOR}[op]
    return _paper_segments(pathops.op(a, _skia(db), kind, fix_winding=True))


@pytest.fixture
def paper_adapter(monkeypatch):
    monkeypatch.setattr(comp, "pathops", pj)
    pj.set_backend(_fake_paper)
    yield
    pj.set_backend(None)


def _area(contours):
    return abs(comp._path(contours).area) if contours else 0.0


@pytest.mark.parametrize("path,glyphs", [
    ("examples/sans/font.py", ["o", "a", "g", "B", "e", "eight", "percent", "aring", "ampersand", "Q"]),
    ("examples/display_serif/font.py", ["o", "a", "g", "e", "R", "eight", "at"]),
])
def test_adapter_compiles_like_skia(paper_adapter, path, glyphs):
    font = load_font(ROOT / path)
    with_js = compile_font(font, glyphs=glyphs)
    pj.set_backend(None)
    comp.pathops = pathops                      # the real one, for the reference
    ref = compile_font(font, glyphs=glyphs)
    for g in glyphs:
        a, b = with_js.glyphs[g], ref.glyphs[g]
        assert len(a.contours) == len(b.contours), g
        assert _area(a.contours) == pytest.approx(_area(b.contours), rel=1e-3), g
        # outer counter-clockwise, holes clockwise: the signed areas match skia's
        assert sorted(round(c.area()) for c in a.contours) == pytest.approx(
            sorted(round(c.area()) for c in b.contours), rel=1e-3), g
        assert a.advance == b.advance


def test_svg_roundtrip_and_reverse():
    p = pj.Path()
    pen = p.getPen()
    pen.moveTo((0, 0)); pen.lineTo((100, 0)); pen.curveTo((120, 0), (130, 50), (100, 100)); pen.lineTo((0, 100))
    pen.closePath()
    c = p._contours[0]
    r = pj._reverse(c)
    assert pj._signed_area(r) == pytest.approx(-pj._signed_area(c))
    assert pj._reverse(r) == c


def test_no_backend_outside_pyodide():
    pj.set_backend(None)
    p = pj.Path()
    p.getPen().moveTo((0, 0))
    with pytest.raises(pj.PathOpsError):
        p.simplify()
