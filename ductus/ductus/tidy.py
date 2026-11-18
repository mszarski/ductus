"""Outline tidying by rule: the small leftovers of overlapping strokes.

When one stroke ends inside another a few units off its edge, the merged
outline keeps the difference: a step, a nub or a needle spike a few units
long where the eye expects one clean edge. A font may declare::

    font.tidy = {"step": 12, "spike": 150}

and after each glyph is merged (before any ink traps):

* **steps and nubs** -- two corners joined by a segment (straight or curved)
  whose chord is shorter than ``step`` units collapse into one point at its
  middle, so the edges either side meet directly;
* **spikes** -- an on-curve point turning more than ``spike`` degrees between
  two straight segments, one of them shorter than four ``step``\\ s, is removed.

Corners are on-curve points where the outline turns by more than 25 degrees.
Nothing longer than ``step`` is touched, so real details (a cut terminal's
face, a serif) survive. Off unless a font declares it.
"""
from __future__ import annotations

import dataclasses
import math

from .geometry import Contour


def _turn(a, b):
    la, lb = math.hypot(*a), math.hypot(*b)
    if la < 1e-9 or lb < 1e-9:
        return 0.0
    c = max(-1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / (la * lb)))
    return math.degrees(math.acos(c))


def _vec(p, q):
    return (q[0] - p[0], q[1] - p[1])


def tidy_contour(c: Contour, step: float, spike: float) -> Contour:
    pts, types, names = [list(p) for p in c.pts], list(c.types), list(c.names)
    changed = True
    while changed and len(pts) > 3:
        changed = False
        n = len(pts)
        on = [k for k in range(n) if types[k] == "on"]
        for k, i in enumerate(on):
            j = on[(k + 1) % len(on)]                       # the next on-curve point (a line or a curve)
            p, q = pts[i], pts[j]
            seg = _vec(p, q)
            L = math.hypot(*seg)
            if L < 1e-9 or L >= step or len(on) < 4:
                continue
            # the turns into and out of the short segment, against its chord
            t_in = _turn(_vec(pts[i - 1], p), seg)
            t_out = _turn(seg, _vec(q, pts[(j + 1) % n]))
            if t_in < 25 or t_out < 25:
                continue
            # collapse: the segment (and any handles on it) becomes one point at its middle
            mid = [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2]
            drop = [(i + d) % n for d in range(1, (j - i) % n + 1)]       # handles between, and q
            pts[i] = mid
            for d in sorted(drop, reverse=True):
                del pts[d], types[d], names[d]
            changed = True
            break
        if changed:
            continue
        n = len(pts)
        for i in range(n):
            if types[i] != "on" or types[i - 1] != "on" or types[(i + 1) % n] != "on":
                continue                                    # spikes between two straight segments only
            a, b = _vec(pts[i - 1], pts[i]), _vec(pts[i], pts[(i + 1) % n])
            if _turn(a, b) > spike and min(math.hypot(*a), math.hypot(*b)) < 4 * step:
                del pts[i], types[i], names[i]
                changed = True
                break
    if types and types[0] != "on":                          # keep the contour starting on-curve
        k = types.index("on")
        pts, types, names = pts[k:] + pts[:k], types[k:] + types[:k], names[k:] + names[:k]
    for p in pts:
        p[0], p[1] = float(round(p[0])), float(round(p[1]))
    return Contour(pts, types, names)


def tidy_glyph(g, step: float, spike: float):
    if not g.contours:
        return g
    contours = [tidy_contour(c, step, spike) for c in g.contours]
    contours = [c for c in contours if len(c.pts) >= 3 and abs(c.area()) >= 40.0]
    if [c.pts for c in contours] == [c.pts for c in g.contours]:
        return g
    from .compile import _bounds
    return dataclasses.replace(g, contours=contours, bounds=_bounds(contours) or g.bounds,
                               signature="|".join(c.signature() for c in contours))


def apply(cf, font):
    """The compiled font with ``font.tidy``'s rule applied to every glyph."""
    spec = getattr(font, "tidy", None)
    if not spec:
        return cf
    step, spike = float(spec.get("step", 12)), float(spec.get("spike", 150))
    return dataclasses.replace(cf, glyphs={n: tidy_glyph(g, step, spike) for n, g in cf.glyphs.items()})
