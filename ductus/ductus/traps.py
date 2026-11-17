"""Ink traps by rule: notches cut into a glyph's sharp inner crotches.

A font declares them::

    font.traps = {"depth": "trap_depth", "mouth": "trap_mouth", "angle": "trap_angle"}

each value a number or the name of a font parameter (and ``"skip"``: glyphs
left untrapped, e.g. commas, whose dot-to-tail joint is no crotch). After a glyph is merged,
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


def corners(c: Contour, max_angle: float, min_angle: float = 6.0, min_turn: float = 25.0):
    """The trap sites of a contour: (corner, incoming dir, outgoing dir, into-ink dir) for each
    sharp concave on-curve corner whose white angle is between min_angle and max_angle.
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
        u = _unit(a[0] - b[0], a[1] - b[1])                 # into the ink, bisecting its reflex angle
        out.append((tuple(p), a, b, u))
    return out


def trap_cuts(contours, depth: float, mouth: float, max_angle: float) -> list[Contour]:
    """The notch triangles for every trap site of ``contours``."""
    cuts = []
    for c in contours:
        for (px, py), a, b, u in corners(c, max_angle):
            A = (px - a[0] * mouth, py - a[1] * mouth)      # back along the arriving edge
            B = (px + b[0] * mouth, py + b[1] * mouth)      # on along the leaving edge
            C = (px + u[0] * depth, py + u[1] * depth)      # the tip, inside the ink
            t = Contour()
            t.add(A, "on", "trap.a")
            t.add(C, "on", "trap.tip")
            t.add(B, "on", "trap.b")
            cuts.append(t)
    return cuts


def trap_glyph(g, depth: float, mouth: float, max_angle: float):
    """The compiled glyph with its crotches trapped."""
    if depth <= 0 or not g.contours:
        return g
    cuts = trap_cuts(g.contours, depth, mouth, max_angle)
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
    skip = set(spec.get("skip", ()))
    glyphs = {n: g if n in skip else trap_glyph(g, depth, mouth, angle) for n, g in cf.glyphs.items()}
    return dataclasses.replace(cf, glyphs=glyphs)
