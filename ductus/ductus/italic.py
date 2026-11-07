"""Italics by rules (SPEC M6): a corrected oblique derived from the upright.

A font declares its rules::

    font.italic = {
        "angle": 10,                       # degrees the verticals lean
        "round": "o O c C e Q ...",        # glyphs drawn mostly as bowls
        "round_k": 0.5,                    # share of their slant done by rotation, not shear
        "origin": None,                    # y the slant turns about (default: half the x-height)
        "params": lambda values: {...},    # optional parameter corrections (e.g. stems by 1/cos)
        "kerning": {"default": {...}, 700: {...}},   # italic kerning, from `ductus kern --italic`
    }

The rules, applied to the finished upright glyph:

* **Spacing first, then slant.** Every glyph is spaced upright and slanted
  about ``origin`` (half the x-height), so it stays centred in its advance
  where the eye judges it; the advance is unchanged.
* **Round glyphs are rotated, not only sheared.** A pure shear tilts a
  bowl's stress and thins two opposite quarters: the bowl looks lopsided.
  Round glyphs are first rotated clockwise by ``round_k`` x the angle about
  their ink centre, then sheared by the rest (``tan(angle) - tan(k angle)``),
  so their verticals end at the same slant as the stems'. They are then
  re-scaled vertically to their upright height, so overshoots and
  alignment hold. Accented letters follow their base (the accent rotates
  with it).
* **Optional parameter corrections** (``params``): e.g. stems widened by
  ``1/cos(angle)`` so slanted stems keep their measured weight.

The transforms are affine per glyph, so an italic master stays
point-compatible with the other italic masters (variable italics work as
the upright ones do).
"""
from __future__ import annotations

import contextvars
import dataclasses
import math
from contextlib import contextmanager

_ITALIC: contextvars.ContextVar[bool] = contextvars.ContextVar("ductus_italic", default=False)


@contextmanager
def italic_mode(on: bool = True):
    """Compile everything inside as italic (``compile_font`` checks it)."""
    token = _ITALIC.set(on)
    try:
        yield
    finally:
        _ITALIC.reset(token)


def active(font) -> bool:
    return _ITALIC.get() and bool(getattr(font, "italic", None))


def round_names(font) -> set[str]:
    spec = font.italic.get("round", "")
    names = set(spec.split()) if isinstance(spec, str) else set(spec)
    # accented letters follow their base
    for cname, cspec in getattr(font, "composites", {}).items():
        if cspec.get("base") in names:
            names.add(cname)
    return names


def param_corrections(font, values: dict) -> dict:
    fn = font.italic.get("params") if getattr(font, "italic", None) else None
    return dict(fn(values)) if fn else {}


def _bounds(contours):
    xs = [p[0] for c in contours for p in c.pts]
    ys = [p[1] for c in contours for p in c.pts]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _curve_ys(contours):
    """Lowest and highest y on the outline itself (curves sampled finely)."""
    from .bench.metrics import sample_outline
    ys = sample_outline(contours, step=0.5)[:, 1]
    return float(ys.min()), float(ys.max())


def _transform(contours, fn):
    out = []
    for c in contours:
        cc = c.copy()
        for p in cc.pts:
            p[0], p[1] = fn(p[0], p[1])
        out.append(cc)
    return out


def slant_glyph(g, angle: float, y0: float, rotate_k: float = 0.0):
    """The glyph slanted by ``angle`` degrees about height ``y0``; with
    ``rotate_k`` the first share of the slant is a rotation about the ink
    centre, then a vertical re-scale back to the upright height."""
    if not g.contours:
        return g
    th = math.radians(angle)
    contours = g.contours
    b = _bounds(contours)
    shear = math.tan(th)
    if rotate_k:
        a = rotate_k * th
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        ca, sa = math.cos(a), math.sin(a)
        # clockwise rotation: the top moves right
        contours = _transform(contours, lambda x, y: (cx + (x - cx) * ca + (y - cy) * sa,
                                                      cy - (x - cx) * sa + (y - cy) * ca))
        # back to the upright height, measured on the curves (not the control points), so the
        # overshoots land exactly where the upright's do
        y_lo, y_hi = _curve_ys(g.contours)
        r_lo, r_hi = _curve_ys(contours)
        sy = (y_hi - y_lo) / (r_hi - r_lo) if r_hi > r_lo else 1.0
        contours = _transform(contours, lambda x, y: (x, y_lo + (y - r_lo) * sy))
        shear = math.tan(th) - math.tan(a)
    contours = _transform(contours, lambda x, y: (round(x + (y - y0) * shear, 2), round(y, 2)))
    pieces = _transform(g.pieces, lambda x, y: (x + (y - y0) * math.tan(th), y)) if g.pieces else g.pieces
    nb = _bounds(contours)
    return dataclasses.replace(g, contours=contours, bounds=nb, pieces=pieces,
                               lsb=nb[0], rsb=g.advance - nb[2])


def italicize(cf, font, loc=None):
    """The compiled font made italic by ``font.italic``'s rules."""
    spec = font.italic
    angle = float(spec.get("angle", 10))
    y0 = spec.get("origin")
    y0 = float(y0) if y0 is not None else cf.metrics["xheight"] / 2
    k = float(spec.get("round_k", 0.5))
    rounds = round_names(font)
    glyphs = {n: slant_glyph(g, angle, y0, k if n in rounds else 0.0) for n, g in cf.glyphs.items()}
    kern = spec.get("kerning", {})
    kerning = kern.get(loc if loc is not None else "default", kern.get("default"))
    if kerning is not None:
        kerning = {(a, b): v for (a, b), v in kerning.items() if a in glyphs and b in glyphs}
    else:
        kerning = cf.kerning
    style = "Italic" if cf.style in ("Regular", "") else f"{cf.style} Italic"
    return dataclasses.replace(cf, glyphs=glyphs, style=style, kerning=kerning, italic_angle=-angle)
