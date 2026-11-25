# The language

A Ductus font is a Python module, conventionally `font.py`. It makes a
`Font`, declares parameters, and defines glyphs from strokes and parts.
`ductus build font.py` loads the module and compiles it:

```
parameters → skeletons (parts) → skeleton overrides → broad-nib expansion → terminals
           → outline overrides → overlap removal, direction, rounding → spacing → .otf
```

`compile_font(font, params, overrides)` is a pure function. It returns a
`CompiledFont`, which holds outlines, skeletons, named points and metrics,
and can be serialised to JSON (`ductus build --json`).

## Parameters

```python
from ductus import param

stem     = param(80,   range=(30, 180))
contrast = param(0.45, range=(0.0, 0.9))
n_width  = counter + stem        # arithmetic builds an expression, evaluated at compile time
```

A parameter is a named default value with an optional range:
- the range sets the editor's slider;
- it bounds `ductus fit`;
- `ductus test` sweeps every ranged parameter to both ends.

Expressions over parameters stay lazy, so changing `stem` once moves every
glyph that depends on it. `--set stem=120` on the command line, or a
master's settings in a variable font, simply supply other values.

## Pens

```python
from ductus import Pen
font.pen = Pen(angle=20, width=stem, contrast=contrast, inside=0.72)
```

Strokes are expanded by a broad-nib pen. The width of the mark depends on
the direction of travel θ:

```
w(θ) = hair + k · |sin(θ − angle)|,   hair = width · (1 − contrast)
```

`k` is chosen so that a vertical stroke is exactly `width`; the stem lint
checks exactly this.
- `contrast` 0 is monoline.
- `angle` 0 is a level nib: thick verticals, thin horizontals.
- `inside` (closed strokes): the share of the modulation placed on the
  counter side.

Any stroke can carry its own `pen=`. The pen angle can also turn along a
stroke: give a node a `pen_angle`.

## Strokes

Inside a glyph or part, `g` (or `p`) is a builder:

```python
g.line((0, 0), (0, xheight), name="stem", names=("bottom", "top"))

(g.path(name="arch", profile=taper(), bias=0.4)
    .start((x, y0), name="join", dir=68, terminal=False)
    .curve_to((x + w * 0.53, top), name="shoulder", dir=0)
    .curve_to((x + w, top - drop), name="shoulder_out", dir=-90)
    .line_to((x + w, 0), name="leg"))
```

- **Nodes.** Each node takes a name, a direction of travel `dir` (degrees),
  a Hobby `tension`, a local width delta `width`, a `pen_angle`, and a
  `terminal`:
  - `True`: the font's default end;
  - `False`: no terminal, as for an end hidden inside another stroke;
  - a tag such as `"foot"`, looked up in the terminal set.
- **Curves.** Skeleton curves use Hobby's handle lengths. `smooth=True`
  solves the directions for continuous curvature (METAFONT-style).
- **Width.** A **profile** varies the width along the stroke: a knot curve
  over t in [0, 1], eased with smoothstep. The helpers are `constant()`,
  `taper()` and `swell()` (in `ductus.profiles`). **bias** sets the share of
  the modulation left of the direction of travel.
- **Closed paths** end with `.close()`.
- **Fixed point structure.** Each side of an expanded stroke is fitted with
  a fixed four cubics per skeleton curve. Point structure therefore never
  depends on parameter values: every setting of a font is
  point-compatible before the overlaps are merged.

## Parts and inheritance

```python
from ductus import part, glyph

@part
def arch(p, x, width, top=xheight):
    ...

@glyph("n")
def n(g):
    g += stem_(x=0, top=xheight)
    g += arch(x=0, width=n_width)

@glyph("m")
def m(g):
    g += stem_(x=0, top=xheight)
    g += arch(x=0, width=w, name="arch1")
    g += arch(x=w, width=w, name="arch2")

@glyph("h")
def h(g):
    g.inherit("n")
    g["stem"].top = ascender
```

A part is a deferred call: `g += arch(...)` records it and runs it later.
`g.inherit("n")` copies n's calls, so `g["stem"].top = ...` edits an
argument before anything is drawn. Inherited glyphs are re-scoped
(`h.arch.shoulder`), and **overrides are not inherited**. Pass `name=` to
use one part twice in a glyph.

## Contour parts

Some shapes are better described as contours than as pen strokes:

| Primitive | Call | Used for |
|---|---|---|
| bowl | `g.bowl(left, right, bottom, top, thick, thin, fullness=(h, v), inner_fullness=..., stress=, rotate=)` | o O b e and the g's loops |
| lobe | `g.lobe(edge_x, side, far, bottom, top_join, bottom_join, thick, thin_bottom, ...)` | a bowl closed by a stem: a, d, q, b, p |
| join | `join(at, thin, angle, notch)` | how an arch or lobe meets a stem: crotch height, thickness, angle, notch |
| contour | `g.contour("name").move(p).line(q)...close()` | polygons: flags, wedges, symbols |
| cut | `g.cut("name").move(p)...close()` | subtracted after overlap removal: e and G apertures, flat cuts |

A bowl is an outer contour and a counter, each with four named extrema
(`o.bowl.outer.top`, `o.bowl.inner.left`, and so on) and four cubic
quadrants.
- **`fullness`** is the handle length as a share of the quadrant (0.552 is
  an ellipse). An `(h, v)` pair gives the superellipse's two independent
  exponents.
- **`stress`** rotates the counter's extrema.

## Terminals

Stroke ends are styled by the font's terminal function, so the same
construction makes a serif or a sans:

```python
from ductus import serifs
font.terminals = serifs.none                                   # cut square
font.terminals = serifs.Set(serifs.bracketed(length=40, bracket=30),
                            foot=serifs.bracketed(length=60),  # ends tagged "foot"
                            head=serifs.wedge(side="left"))
```

The library offers `none`, `flat(axis)`, `bracketed`, `wedge`, `beak`,
`ball` and `slab`. All of them are aware of the world axes, so a serif on a
diagonal stays level.

## Composites

```python
font.composite("aacute", "a", ["acutecomb"])     # base + marks, centred on the ink
font.combine("ae", [("a", 0, 0), ("e", 420, 0)])  # glyphs set side by side and merged
font.turn("questiondown", "question", dy=-180)    # turned 180 degrees
font.slant("at", 12)                               # an italic form inside an upright face
```

The compiler copies the outlines, so a composite is an ordinary glyph in
the font.
- **Marks** are drawn at the lowercase position, and lifted by cap height
  minus x-height on capitals.
- **Kerning.** Composites take their base's kerning weights.

## Overrides

Hand adjustments are deltas on named points, kept in `overrides.yaml`
beside `font.py`. The editor writes them when you drag:

```yaml
n.arch.shoulder:      { dx: 12, dy: 0 }                     # move a skeleton point
n.arch.join:          { dx: 0, dy: 0, dw: -18, da: -8 }     # thinner, steeper join
o.bowl.top:           { dx: 0, dy: 0, dt: 0.15 }            # flatter curve through the top
m.arch2.shoulder_out: { dx: -6, dy: 4, stage: outline }     # move both expanded points
o.lsb:                { dx: 6, dy: 0 }                      # side bearing
n.@serif_len:         { dv: 8 }                             # a parameter changed for this glyph only
```

| Key | What it changes |
|---|---|
| `dx`, `dy` | moves the point |
| `dw` | the stroke width at the node (interpolated along the neighbouring segments) |
| `da` | rotates the direction of travel |
| `dt` | Hobby tension on both sides of the node |
| `dv` | a parameter, for one glyph |
| `stage: outline` | moves expanded outline points rather than the skeleton |

None of them changes point structure, so they are safe for interpolation.
A variable font can also have per-master overrides
(`overrides_<value>.yaml`, added on top).

Prefer a parameter or a kit option to an override. Several glyphs
overriding the same thing means the shared value, or the primitive, is
wrong.

## Names

Points are named `glyph.instance[.stroke].node`, for example
`n.arch.shoulder`. Expanded outline points add `.l` or `.r`. A part that
draws a single stroke collapses to `glyph.instance.node`. Duplicate names
are a compile error. Points created by overlap removal are unnamed and
cannot be overridden.
