"""The subset of skia-pathops the compiler uses, backed by Paper.js (SPEC M7).

skia-pathops is a C++ extension with no Pyodide build, so in the browser
:mod:`ductus.compile` falls back to this module (``import pathops`` fails).
Paper.js does boolean operations on curves (it keeps the Beziers) in
JavaScript; this module sends it SVG path data and reads back its segments.

Only what ``compile.merge`` needs is provided: ``Path`` (``getPen``,
``simplify``, ``draw``), ``op``, ``PathOp`` and ``PathOpsError``. Results are
re-oriented the way skia's ``clockwise=False`` leaves them: outer contours
counter-clockwise (y up), holes clockwise.

Transports for the JavaScript side, in order:

* **Pyodide** (the browser): ``globalThis.__ductusBool`` defined by
  :data:`JS_SOURCE` through ``pyodide.code.run_js``; Paper.js must be loaded
  in the page (``paper-core.js``).
* :func:`set_backend`: any callable ``(path_a, path_b, op) -> segments``
  (tests use it to check this module's glue against skia-pathops).
"""
from __future__ import annotations

import enum
import json

JS_SOURCE = r"""
globalThis.__ductusBool = function (dA, dB, op) {
  if (!globalThis.__ductusPaperReady) { paper.setup(new paper.Size(1, 1)); globalThis.__ductusPaperReady = true; }
  const mk = (d) => new paper.CompoundPath({pathData: d, insert: false, fillRule: 'nonzero'});
  // Two closed outlines cross an even number of times; an odd count means Paper missed a tangent crossing
  // (the display t's cut removed nothing). Then the second shape is nudged by 0.01 u -- invisible once
  // the outline is rounded to the grid -- and the operation retried.
  const guarded = (fn, a, b) => {
    if (a.getIntersections(b).length % 2 === 1) {
      b = b.clone({insert: false});
      b.translate(new paper.Point(0.013, 0.007));
    }
    return fn(a, b);
  };
  const unite = (a, b) => guarded((x, y) => x.unite(y, {insert: false}), a, b);
  const subtract = (a, b) => guarded((x, y) => x.subtract(y, {insert: false}), a, b);
  // Paper's self-union (unite with an empty path) mis-resolves overlapping sub-paths (the v's strokes
  // lost or gained area, and a later subtract emptied the glyph). Instead: each hole goes to the smallest
  // outer contour containing it, each outer minus its holes, then the shapes united one by one --
  // the non-zero fill of the input, which pairwise unions resolve correctly.
  const simplify = (cp) => {
    // degenerate pieces (zero area) derail a later subtract; drop them
    const kids = ((cp.children && cp.children.length) ? cp.children.slice() : [cp]).filter(k => Math.abs(k.area) >= 1);
    if (!kids.length) return new paper.Path({insert: false});
    const big = kids.reduce((m, k) => Math.abs(k.area) > Math.abs(m.area) ? k : m);
    const outers = kids.filter(k => Math.sign(k.area) === Math.sign(big.area));
    const holes = kids.filter(k => Math.sign(k.area) !== Math.sign(big.area));
    const own = new Map(outers.map(o => [o, []]));
    for (const h of holes) {
      const ip = h.interiorPoint;
      // the host holds the whole hole (a stroke crossing a counter, like the e's bar, holds only part of it)
      const host = outers.filter(o => o.bounds.contains(h.bounds) && o.contains(ip)
                                     && h.segments.every(sg => o.contains(sg.point)))
                         .sort((x, y) => Math.abs(x.area) - Math.abs(y.area))[0];
      if (host) own.get(host).push(h);
    }
    // largest first: pairwise unions of small pieces sharing edges (serifs on strokes) can lose area
    outers.sort((x, y) => Math.abs(y.area) - Math.abs(x.area));
    let r = new paper.Path({insert: false});
    for (const o of outers) {
      let shape = o.clone({insert: false});
      for (const h of own.get(o)) shape = subtract(shape, h.clone({insert: false}));
      r = unite(r, shape);
    }
    return r;
  };
  const a = mk(dA);
  let r;
  if (op === 'simplify') r = simplify(a);
  else {
    const b = mk(dB);
    r = op === 'union' ? unite(a, b) : op === 'difference' ? subtract(a, b)
      : op === 'intersection' ? guarded((x, y) => x.intersect(y, {insert: false}), a, b)
      : guarded((x, y) => x.exclude(y, {insert: false}), a, b);
  }
  const kids = r.children ? r.children : [r];
  const out = [];
  for (const p of kids) {
    if (!p.segments || p.segments.length < 2) continue;
    out.push(p.segments.map(s => [s.point.x, s.point.y, s.handleIn.x, s.handleIn.y, s.handleOut.x, s.handleOut.y]));
  }
  return JSON.stringify(out);
};
"""


class PathOpsError(Exception):
    pass


class PathOp(enum.Enum):
    UNION = "union"
    DIFFERENCE = "difference"
    INTERSECTION = "intersection"
    XOR = "xor"


_backend = None


def set_backend(fn):
    """Use ``fn(path_data_a, path_data_b, op) -> list of contours of Paper
    segments [x, y, in_dx, in_dy, out_dx, out_dy]`` (None: the default)."""
    global _backend
    _backend = fn


def _js_backend():
    from pyodide.code import run_js        # only importable inside Pyodide
    import js
    if not hasattr(js, "__ductusBool"):
        run_js(JS_SOURCE)

    def call(da, db, op):
        return json.loads(js.__ductusBool(da, db, op))
    return call


def node_backend(paper_js: str):
    """A backend running the real Paper.js in a persistent Node process (tests and
    debugging outside the browser): ``set_backend(node_backend("paper-core.js"))``."""
    import subprocess
    src = (f"const paper = require({json.dumps(str(paper_js))});\n" + JS_SOURCE +
           "\nconst rl = require('readline').createInterface({input: process.stdin});\n"
           "rl.on('line', (l) => { const [a, b, op] = JSON.parse(l); let out;\n"
           "  try { out = __ductusBool(a, b, op); } catch (e) { out = JSON.stringify({error: String(e)}); }\n"
           "  process.stdout.write(out + '\\n'); });\n")
    proc = subprocess.Popen(["node", "-e", src], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    def call(da, db, op):
        proc.stdin.write(json.dumps([da, db, op]) + "\n")
        proc.stdin.flush()
        r = json.loads(proc.stdout.readline())
        if isinstance(r, dict):
            raise PathOpsError(r["error"])
        return r
    return call


def _call(da: str, db: str, op: str):
    global _backend
    if _backend is None:
        try:
            _backend = _js_backend()
        except ImportError as e:
            raise PathOpsError("no boolean backend: skia-pathops is not installed and this is not Pyodide") from e
    try:
        return _backend(da, db, op)
    except Exception as e:                  # Paper.js threw
        raise PathOpsError(str(e)) from e


# ---- paths ----------------------------------------------------------------

class _Pen:
    def __init__(self, path):
        self.path = path

    def moveTo(self, p):
        self.path._contours.append([("M", tuple(p))])

    def lineTo(self, p):
        self.path._contours[-1].append(("L", tuple(p)))

    def curveTo(self, *pts):
        if len(pts) != 3:
            raise PathOpsError("only cubic curveTo is supported")
        self.path._contours[-1].append(("C", tuple(pts[0]), tuple(pts[1]), tuple(pts[2])))

    def qCurveTo(self, *pts):
        # one quadratic segment (with its end point) -> the equivalent cubic
        if len(pts) != 2 or pts[-1] is None:
            raise PathOpsError("only single quadratic segments are supported")
        c = self.path._contours[-1]
        p0 = c[-1][-1]
        q, p = pts
        c1 = (p0[0] + 2 / 3 * (q[0] - p0[0]), p0[1] + 2 / 3 * (q[1] - p0[1]))
        c2 = (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1]))
        c.append(("C", c1, c2, tuple(p)))

    def closePath(self):
        pass

    def endPath(self):
        pass


class Path:
    """A list of closed contours of M / L / C commands."""

    def __init__(self):
        self._contours: list[list[tuple]] = []

    def getPen(self):
        return _Pen(self)

    def to_svg(self) -> str:
        parts = []
        for c in self._contours:
            for cmd in c:
                if cmd[0] in "ML":
                    parts.append(f"{cmd[0]}{cmd[1][0]:.4f},{cmd[1][1]:.4f}")
                else:
                    parts.append("C" + " ".join(f"{x:.4f},{y:.4f}" for x, y in cmd[1:]))
            parts.append("Z")
        return " ".join(parts)

    def draw(self, pen):
        for c in self._contours:
            pen.moveTo(c[0][1])
            for cmd in c[1:]:
                if cmd[0] == "L":
                    pen.lineTo(cmd[1])
                else:
                    pen.curveTo(cmd[1], cmd[2], cmd[3])
            pen.closePath()

    def simplify(self, fix_winding=True, keep_starting_points=True, clockwise=False):
        self._contours = _from_segments(_call(self.to_svg(), "", "simplify"))

    @property
    def area(self) -> float:
        return sum(abs(_signed_area(c)) for c in self._contours)


def op(a: Path, b: Path, operation: PathOp, fix_winding=True, keep_starting_points=True, clockwise=False) -> Path:
    out = Path()
    out._contours = _from_segments(_call(a.to_svg(), b.to_svg(), operation.value))
    return out


# ---- reading Paper's result -----------------------------------------------

def _from_segments(contours) -> list[list[tuple]]:
    """Paper segments (point, handleIn, handleOut; handles relative) -> M/L/C
    contours, then oriented outer CCW / holes CW (y up)."""
    out = []
    for segs in contours:
        n = len(segs)
        if n < 2:
            continue
        c = [("M", (segs[0][0], segs[0][1]))]
        for i in range(n):
            s0, s1 = segs[i], segs[(i + 1) % n]
            p0, p1 = (s0[0], s0[1]), (s1[0], s1[1])
            ho, hi = (s0[4], s0[5]), (s1[2], s1[3])
            if i == n - 1 and ho == (0, 0) and hi == (0, 0):
                break                                   # the closing line: implied by closePath
            if ho == (0, 0) and hi == (0, 0):
                c.append(("L", p1))
            else:
                c.append(("C", (p0[0] + ho[0], p0[1] + ho[1]), (p1[0] + hi[0], p1[1] + hi[1]), p1))
        out.append(c)
    return _orient(out)


def _poly(c, k=8):
    """The contour flattened (curves sampled k times)."""
    pts = [c[0][1]]
    for cmd in c[1:]:
        if cmd[0] == "L":
            pts.append(cmd[1])
        else:
            p0, c1, c2, p1 = pts[-1], cmd[1], cmd[2], cmd[3]
            for j in range(1, k + 1):
                t = j / k
                mt = 1 - t
                pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t ** 3 * p1[0],
                            mt ** 3 * p0[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t ** 3 * p1[1]))
    return pts


def _signed_area(c) -> float:
    pts = _poly(c)
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def _inside(pt, poly) -> bool:
    x, y = pt
    inside = False
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def _reverse(c):
    """The same contour traversed backwards (the implied closing line reverses with it)."""
    pts = [c[0][1]] + [cmd[-1] for cmd in c[1:]]
    out = [("M", pts[-1])]
    for k in range(len(c) - 1, 0, -1):
        cmd, start = c[k], pts[k - 1]
        out.append(("L", start) if cmd[0] == "L" else ("C", cmd[2], cmd[1], start))
    return out


def _orient(contours):
    polys = [_poly(c) for c in contours]
    out = []
    for i, c in enumerate(contours):
        probe = polys[i][0]
        depth = sum(1 for j, p in enumerate(polys) if j != i and _inside(probe, p))
        want_ccw = depth % 2 == 0
        if (_signed_area(c) > 0) != want_ccw:
            c = _reverse(c)
        out.append(c)
    return out
