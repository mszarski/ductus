"""Ink traps by rule: notches cut into a glyph's sharp inner crotches.

A font declares them::

    font.traps = {"depth": "trap_depth", "mouth": "trap_mouth", "angle": "trap_angle"}

each value a number or the name of a font parameter; also ``"min_angle"``
(narrower crotches are already slivers: a trap there reads as a crack),
``"min_edge"`` (both edges of a crotch must run this far; default 1.5 mouths)
and ``"skip"`` (glyphs left untrapped, e.g. commas, whose dot-to-tail joint
is no crotch). After a glyph is merged,
every sharp concave corner of its outline -- where the white wedges into the ink
at less than ``angle`` degrees (an arch leaving a stem, the inside of a v's
vertex, a lobe meeting its stem, the crotches of k, x, y) -- gets a triangular
notch: its mouth on the two edges ``mouth`` units from the corner, its tip
``depth`` units into the ink along the corner's bisector. In type made for
small sizes and poor printing these keep the crotches from filling in; at
display sizes they are a style.

The rule needs no knowledge of how a glyph was built, so it works on every
glyph and face alike, and composites get the same traps as their bases.
Depth 0 (the default) leaves the outline untouched.
"""
from __future__ import annotations

import dataclasses
import math

from .geometry import Contour


def _value(v, params):
    if isinstance(v, str):
        return float(params[v])
    return float(v)


def _unit(x, y):
    n = math.hypot(x, y)
    return (x / n, y / n) if n > 1e-9 else (0.0, 0.0)


def corners(c: Contour, max_angle: float, min_angle: float = 6.0, min_turn: float = 25.0, min_edge: float = 0.0):
    """The trap sites of a contour: (corner, incoming dir, outgoing dir, into-ink dir) for each
    sharp concave on-curve corner whose white angle is between min_angle and max_angle and whose
    two edges each run at least min_edge (a crotch between two strokes, not a little corner).
    Contours run with the ink on their left (outer counter-clockwise, counters clockwise)."""
    n = len(c.pts)
    out = []
    if n < 3:
        return out
    for i in range(n):
        if c.types[i] != "on":
            continue
        p = c.pts[i]
        prev = c.pts[i - 1]
        nxt = c.pts[(i + 1) % n]
        a = _unit(p[0] - prev[0], p[1] - prev[1])          # arriving
        b = _unit(nxt[0] - p[0], nxt[1] - p[1])            # leaving
        if a == (0.0, 0.0) or b == (0.0, 0.0):
            continue
        cross = a[0] * b[1] - a[1] * b[0]
        if cross >= 0:                                      # a left turn: a convex corner of the ink
            continue
        turn = math.degrees(math.acos(max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1]))))
        white = 180.0 - turn
        if turn < min_turn or not (min_angle <= white <= max_angle):
            continue
        if min_edge and (_edge_run(c, i, -1, min_edge) < min_edge or _edge_run(c, i, +1, min_edge) < min_edge):
            continue
        u = _unit(a[0] - b[0], a[1] - b[1])                 # into the ink, bisecting its reflex angle
        out.append((tuple(p), a, b, u))
    return out


def _edge_run(c: Contour, i: int, step: int, limit: float) -> float:
    """How far the outline runs from on-curve point ``i`` (backward for step -1) before the next corner
    (an on-curve point turning more than 25 degrees), along the chords between on-curve points; stops
    counting at ``limit``."""
    on = [k for k, t in enumerate(c.types) if t == "on"]
    n = len(c.pts)
    k = on.index(i)
    run, prev = 0.0, c.pts[i]
    for _ in range(len(on) - 1):
        k = (k + step) % len(on)
        j = on[k]
        q = c.pts[j]
        run += math.hypot(q[0] - prev[0], q[1] - prev[1])
        if run >= limit:
            return run
        a = _unit(q[0] - c.pts[j - 1][0], q[1] - c.pts[j - 1][1])
        b = _unit(c.pts[(j + 1) % n][0] - q[0], c.pts[(j + 1) % n][1] - q[1])
        if math.degrees(math.acos(max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1])))) > 25:
            return run                                  # the next corner: the edge ends here
        prev = q
    return run


def trap_cuts(contours, depth: float, mouth: float, max_angle: float, min_angle: float = 6.0,
              min_edge: float = 0.0) -> list[Contour]:
    """The notch triangles for every trap site of ``contours``."""
    cuts = []
    for c in contours:
        for (px, py), a, b, u in corners(c, max_angle, min_angle, min_edge=min_edge):
            A = (px - a[0] * mouth, py - a[1] * mouth)      # back along the arriving edge
            B = (px + b[0] * mouth, py + b[1] * mouth)      # on along the leaving edge
            C = (px + u[0] * depth, py + u[1] * depth)      # the tip, inside the ink
            t = Contour()
            t.add(A, "on", "trap.a")
            t.add(C, "on", "trap.tip")
            t.add(B, "on", "trap.b")
            cuts.append(t)
    return cuts


def trap_glyph(g, depth: float, mouth: float, max_angle: float, min_angle: float = 6.0, min_edge: float = 0.0):
    """The compiled glyph with its crotches trapped."""
    if depth <= 0 or not g.contours:
        return g
    cuts = trap_cuts(g.contours, depth, mouth, max_angle, min_angle, min_edge)
    if not cuts:
        return g
    from .compile import _bounds, merge
    contours = merge(g.contours, cuts=cuts)
    nb = _bounds(contours) if contours else g.bounds
    return dataclasses.replace(g, contours=contours, bounds=nb, signature="|".join(c.signature() for c in contours),
                               untrapped=g.contours)


def apply(cf, font):
    """The compiled font with ``font.traps``' rule applied to every glyph."""
    spec = getattr(font, "traps", None)
    if not spec:
        return cf
    p = cf.params
    depth = _value(spec.get("depth", 0), p)
    if depth <= 0:
        return cf
    mouth = _value(spec.get("mouth", 12), p)
    angle = _value(spec.get("angle", 75), p)
    # min_angle: crotches narrower than this are already slivers of white, a trap there reads as a crack;
    # min_edge: both edges of a crotch must run this far (default: 1.5 mouths), or it is a little corner
    min_angle = _value(spec.get("min_angle", 6), p)
    min_edge = _value(spec.get("min_edge", 1.5 * mouth), p)
    skip = set(spec.get("skip", ()))
    glyphs = {n: g if n in skip else trap_glyph(g, depth, mouth, angle, min_angle, min_edge)
              for n, g in cf.glyphs.items()}
    return dataclasses.replace(cf, glyphs=glyphs)
