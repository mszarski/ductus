# Getting started

## Install

Ductus needs Python 3.11 or later. Use a virtual environment:

```bash
git clone https://github.com/mszarski/ductus.git
cd ductus/ductus
python -m venv .venv && source .venv/bin/activate
pip install -e ".[proof,validate,serve,test]"
```

The extras are optional:

| Extra | Adds |
|---|---|
| `proof` | proof images (matplotlib, FreeType, Pillow) |
| `validate` | OTS validation of every built font |
| `serve` | the live editor (`ductus serve`) |
| `bench` | measuring against a reference font (`ductus bench`, `ductus fit`) |
| `test` | pytest |

The core needs fontTools, skia-pathops (overlap removal), NumPy, PyYAML and
Typer.

## Build the example faces

```bash
ductus build examples/sans/font.py -o out/                    # DuctusSans-Regular.otf
ductus build examples/sans/font.py --variable -o out/         # wght 300-700 x opsz 8-14
ductus build examples/sans/font.py --italic -o out/           # the italic
ductus build examples/display_serif/font.py --variable -o out/   # opsz 9-72
ductus build examples/notch/font.py --variable -o out/        # wght 300-700
```

Every build is checked twice: fontTools reads the font back, and OTS (the
font sanitiser browsers use) validates it. Install the `validate` extra for
the second check.

## Look at it

```bash
ductus serve examples/notch/font.py        # http://127.0.0.1:8765/
```

The editor compiles the font as you change it. Move a slider to change a
parameter, drag a point to write an override, and type text to see it set
in the freshly built `.otf`. [Tools](tools.md) covers the editor in full.

For a still image:

```bash
ductus proof examples/test_font/font.py --setting "Bold:stem=150" -o proof.png
```

## A first font

`examples/test_font/font.py` is the smallest complete font: `n h m o H O`
and a space. Its core, shortened:

```python
from ductus import Font, Pen, glyph, param, part, serifs

font = Font("Ductus Test", upm=1000)

stem     = param(80,   range=(30, 180))     # ranges become editor sliders and sweep limits
contrast = param(0.45, range=(0.0, 0.9))
xheight  = param(530,  range=(450, 600))

font.pen = Pen(angle=param(20, range=(0, 45)), width=stem, contrast=contrast)
font.xheight = xheight
font.terminals = serifs.none

@part
def stem_(p, x, top, bottom=0):
    p.line((x, bottom), (x, top), name="stem", names=("bottom", "top"))

@part
def arch(p, x, width, top=xheight):
    shoulder_y = top + overshoot - p.pen.width_at(0) / 2
    drop = width * 0.42
    (p.path(name="arch")
        .start((x, shoulder_y - drop * 1.25), name="join", dir=68, terminal=False)
        .curve_to((x + width * 0.53, shoulder_y), name="shoulder", dir=0)
        .curve_to((x + width, shoulder_y - drop), name="shoulder_out", dir=-90)
        .line_to((x + width, 0), name="leg"))

@glyph("n")
def n(g):
    g += stem_(x=0, top=xheight)
    g += arch(x=0, width=counter + stem)
```

Copy that folder, change a value, and build:

```bash
ductus build examples/test_font/font.py --set stem=120 -o out/    # a one-off value
ductus build examples/test_font/font.py --sweep stem=40,160       # and check the outlines stay compatible
ductus test  examples/test_font/font.py                           # every lint, every ranged parameter at both ends
```

A real face is rarely written glyph by glyph like this. The three faces
call the **kit** instead, which already builds about 180 glyphs from a
parameter set; see [Building fonts](building.md). Read
[The language](language.md) next to learn what the kit is made of.

## Run the tests

```bash
pytest
```

The suite compiles every face, lints every glyph, builds the variable
fonts and checks them for compatibility. It takes about two minutes.
