# Building fonts

## The kit

Writing 180 glyphs by hand is how a typeface goes inconsistent. All three
faces instead call `ductus.kits.serif`, where every construction is written
once against a parameter namespace:

```python
from ductus import Font
from ductus.kits import serif as kit

font = Font("Ductus Notch", upm=1000)
P = kit.params(stem=112, hairline=98, xheight=560, capheight=720,
               n_width=455, o_width=560, sb_straight=44, sb_round=30, ...)
kit.define(font, P,
           glyphs="abcdefghijklmnopqrstuvwxyz...",      # which glyphs to build (default: all)
           terminals=kit.sans_set(P),                    # no serifs: ends cut square
           a_style="bowl", a_hood="one", g_style="single", y_tail="straight", at_style="hook")
```

- **`kit.params(**values)`** starts from the kit's defaults, 1,174
  named values each with a range, and replaces the ones you give. An
  unknown name is an error.
- **Terminal sets** make the genre: `kit.sans_set(P)` cuts ends square,
  `kit.bracketed_set(P)` gives bracketed serifs. **Serifs live in the
  terminal set, not in the constructions**, so one kit serves a serif and a
  sans.
- **Style options** of `kit.define` choose between constructions:
  - single- or double-storey g and a;
  - the a's bowl as a lobe, an oval or one stroke;
  - straight or hooked tails, R's leg, Q's tail, the 1's flag;
  - the @, &, cedilla and more.

  Every option defaults to the original outline, so adding one never
  changes an existing face.

Each face's `font.py` in `examples/` reads as a design record: values
grouped by what they do, each with a comment saying why.

## Spacing

- **Side types.** A glyph's sides are `straight` when a vertical stroke sits
  at its edge and `round` otherwise. Each type takes its side bearing from
  `font.sidebearings` (the kit sets them from `sb_straight` and `sb_round`).
- **Per-glyph corrections** are added on top:
  ```python
  font.spacing.update({"f": (-10, -40), "r": (0, -25), "J": (40, 0)})
  ```
  Key glyphs by name (`"AE"`), not by character. A delta also widens an
  empty glyph such as the space.

## Kerning

Kerning is **optical and measured from the font's own outlines**
(`ductus.kerning`), never copied from another font.
- **The measure.** For each pair it takes a power mean of the gaps between
  the two side profiles, and compares that with the gap two flat edges
  would leave.
- **Clearance** only limits how close two outlines may come.

```bash
ductus kern examples/notch/font.py                  # writes kerning.json beside font.py
ductus kern examples/notch/font.py --master 700     # a weight master: kerning_700.json
ductus kern examples/sans/font.py --italic          # the italic: kerning_italic.json
```

The face's `font.py` loads the JSON at its end. The kerner measures the
*unkerned* font, so re-run it after any change to outlines or spacing,
once for every master and italic.

The options that matter most:
- `--clearance`: the closest the outlines may come, in font units.
- `--min-abs`: drop smaller kerns.
- `--strength`: the share of the optical difference to correct.
- `--saturate`: fade the style weights out for pairs that already differ a
  lot.

A face can also have a house style, `kern_style.json`: per-glyph weights
that tighten or loosen its pairs.

## Variable fonts

A face declares an axis, its masters and how each master's parameters
differ from the default:

```python
def _master(params, setting):
    ov = kit.weight_master(params, setting["k"], setting.get("kh"))  # stems x k, horizontals x kh
    ov.update(setting.get("params", {}))                              # then the master's own values
    return ov

font.variable = {
    "tag": "wght", "name": "Weight", "default": 400,
    "masters": {300: {"k": 0.7,  "kh": 0.78, "params": {...}},
                700: {"k": 1.32, "kh": 1.2,  "params": {...}}},
    "params": _master,
    "instances": {"Light": 300, "Regular": 400, "Bold": 700},
    "kerning": {300: {...}, 700: {...}},          # each master's own kerning
}
```

```bash
ductus build examples/notch/font.py --variable -o out/
```

- **Compiling the masters.** Each master is compiled from scratch with its
  own parameters. `kit.weight_master` scales every absolute stroke
  thickness, and widens the gaps between paired strokes so the white
  between them stays.
- **Merging.** The masters are merged into a CFF2 variable font with
  fontTools' `varLib`.
- **Compatibility** (`ductus/compat.py`). Merged outlines are not
  point-compatible across weights, because overlap removal re-segments
  them. The masters are unified exactly first: contours matched, corners
  aligned, curves split at shared positions.
- **Held static.** A real change of structure between masters (a counter
  that closes at the Bold, two marks that touch) can't be interpolated.
  That glyph is held static and reported. Fix it in the design, with the
  master's own values, until nothing is held. A test checks this for every
  face.
- **Per-master hand adjustments** go in a master's `"overrides"`
  (`overrides_700.yaml`).

### A second axis

Ductus Sans adds optical size beside its weight. A master is derived on
every weight master, so the font is a full `wght` × `opsz` grid:

```python
font.variable["second"] = {
    "tag": "opsz", "name": "Optical size", "default": 14,
    "masters": {8: {"k": 1.04, "kh": 1.15, "sb_d": 10, "xh_d": 8}},
    "params": kit.optical_master, "instances": {"Caption": 8},
}
```

`kit.optical_master` derives a text cut by rules: heavier hairlines, a
little more stem, shorter serifs, looser spacing and a larger x-height.
Ductus Display uses it alone, for its `opsz` 9–72 axis.

## Italics

An italic is derived from the upright by rules (`ductus/italic.py`):

```python
font.italic = {
    "angle": 10,                              # degrees the verticals lean
    "round": "o O c C Q zero degree s S",     # glyphs drawn mostly as bowls
    "round_k": 0.5,                           # share of their slant done by rotation, not shear
    "forms": ["a", "f"],                      # optional: true italic forms the kit draws
    "kerning": {...},                         # from `ductus kern --italic`
}
```

```bash
ductus build examples/display_serif/font.py --italic -o out/
ductus build examples/sans/font.py --variable --italic -o out/
```

- **Slant.** Every glyph is spaced upright, then slanted about half the
  x-height, so it stays centred in its advance.
- **Round glyphs** are part rotated and part sheared, which keeps their
  stress balanced, then restored to their upright height.
- **Level strokes.** Glyphs with level strokes (the e's bar, the G's spur)
  must not be in `round`, because rotating would tilt those strokes.
- **True italic forms.** `forms` asks the kit for real italic forms:
  Ductus Display's single-storey a and cursive f.

## Ink traps and tidying

Ductus Notch adds two rules that run on every glyph after its overlaps are
merged:

```python
font.tidy = {"step": 16, "spike": 150, "hole": 120}
font.traps = {"depth": "trap_depth", "mouth": "trap_mouth", "angle": "trap_angle",
              "min_angle": 30, "skip": ["A", "G", "e", "f", "a", "comma", ...]}
```

- **Tidy** (`ductus/tidy.py`) cleans up the leftovers where one stroke ends
  a few units off another's edge:
  - steps and nubs shorter than `step` units collapse;
  - needle spikes are removed;
  - pinhole counters under `hole` square units are filled.
- **Traps** (`ductus/traps.py`) cut a triangular notch into every sharp
  concave corner. A corner qualifies when the white wedges into the ink at
  between `min_angle` and `angle` degrees, and both of its edges run at
  least `min_edge`. The notch's mouth is `mouth` units along each edge and
  its tip is `depth` units into the ink. Values can name parameters, so a
  Bold master can have deeper traps.
  - The rule needs no knowledge of how a glyph was built: composites get
    their base's traps.
  - The stem lint measures the outline as it was before the traps.
  - `skip` lists glyphs whose acute corners are a counter's or a tail's,
    not a crotch between two strokes.

Both are off unless a font declares them.
