"""M4 (optical size) and M6 (italics by rules)."""
import math
from pathlib import Path

import numpy as np
import pytest

from ductus.compile import compile_font
from ductus.emit import build_otf
from ductus.loader import load_font

ROOT = Path(__file__).resolve().parents[1]


# ---- M4: the display serif's text master keeps its hairlines at text size ----

def _hairline_coverage(otf: Path, ch: str, px: int) -> tuple[float, float]:
    """Darkest pixel of the top and bottom hairline on the glyph's centre column (0..1)."""
    freetype = pytest.importorskip("freetype")
    face = freetype.Face(str(otf))
    face.set_pixel_sizes(0, px)
    face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
    bm = face.glyph.bitmap
    a = np.array(bm.buffer, dtype=float).reshape(bm.rows, bm.width) / 255
    col = a[:, a.shape[1] // 2]
    third = max(2, a.shape[0] // 3)
    return float(col[:third].max()), float(col[-third:].max())


def test_text_master_hairlines_hold_at_12px(tmp_path):
    from ductus.variable import compile_master
    font = load_font(ROOT / "examples/display_serif/font.py")
    spec = font.variable
    assert spec["tag"] == "opsz"
    display = compile_font(font, glyphs=["o", "O"])
    text = compile_master(font, compile_font(font).params, spec["masters"][min(spec["masters"])],
                          glyphs=["o", "O"])
    d_otf, t_otf = build_otf(display, tmp_path / "d.otf"), build_otf(text, tmp_path / "t.otf")
    for ch in "oO":
        t_top, t_bot = _hairline_coverage(t_otf, ch, 12)
        d_top, d_bot = _hairline_coverage(d_otf, ch, 12)
        # the text cut's hairlines render at least half dark at 9 pt / 12 px ...
        assert min(t_top, t_bot) >= 0.5, (ch, t_top, t_bot)
        # ... and darker than the display cut's, which grey out there
        assert t_top > d_top and t_bot > d_bot


def test_optical_master_rules():
    from ductus.kits import serif as kit
    params = {"stem": 80.0, "hairline": 30.0, "serif_len": 80.0, "sb_straight": 15.0, "sb_round": 40.0,
              "xheight": 530.0, "arch_contrast": 0.3}
    ov = kit.optical_master(params, {"k": 1.05, "kh": 1.6, "serif_k": 0.85, "sb_d": 18, "xh_d": 10})
    assert ov["hairline"] == pytest.approx(48.0)
    assert ov["stem"] == pytest.approx(84.0)
    assert ov["serif_len"] == pytest.approx(68.0)
    assert ov["sb_straight"] == pytest.approx(33.0) and ov["sb_round"] == pytest.approx(58.0)
    assert ov["xheight"] == pytest.approx(540.0)
    assert ov["arch_contrast"] < 0.3          # heavier hairlines: lower contrast


# ---- M6: a corrected oblique derived by rules ----

@pytest.fixture
def italic_font():
    font = load_font(ROOT / "examples/test_font/font.py")
    font.italic = {"angle": 12, "round": "o O", "round_k": 0.5}
    return font


def test_italic_keeps_advances_and_slants_stems(italic_font):
    up = compile_font(italic_font)
    it = compile_font(italic_font, italic=True)
    assert it.style == "Italic" and it.italic_angle == -12
    for name in up.glyphs:
        assert it.glyphs[name].advance == up.glyphs[name].advance
    # a stem's top moves right of its foot by tan(angle) x its height
    H_up, H_it = up.glyphs["H"].contours, it.glyphs["H"].contours
    xs_top = lambda cs, y: [p[0] for c in cs for p in c.pts if abs(p[1] - y) < 0.6]
    top, foot = max(p[1] for c in H_up for p in c.pts), 0.0
    lean = (min(xs_top(H_it, top)) - min(xs_top(H_up, top))) - (min(xs_top(H_it, foot)) - min(xs_top(H_up, foot)))
    assert lean == pytest.approx(math.tan(math.radians(12)) * top, abs=1.0)


def test_italic_round_glyphs_keep_their_height(italic_font):
    up = compile_font(italic_font, glyphs=["o", "O"])
    it = compile_font(italic_font, glyphs=["o", "O"], italic=True)
    from ductus.italic import _curve_ys
    for name in ("o", "O"):
        # measured on the curves: the overshoots stay where the upright's are
        lo_u, hi_u = _curve_ys(up.glyphs[name].contours)
        lo_i, hi_i = _curve_ys(it.glyphs[name].contours)
        assert lo_i == pytest.approx(lo_u, abs=0.6) and hi_i == pytest.approx(hi_u, abs=0.6)


def test_italic_otf_is_flagged(italic_font, tmp_path):
    from fontTools.ttLib import TTFont
    cf = compile_font(italic_font, italic=True)
    t = TTFont(build_otf(cf, tmp_path / "i.otf"))
    assert t["post"].italicAngle == -12
    assert t["OS/2"].fsSelection & 0x01 and not t["OS/2"].fsSelection & 0x40
    assert t["head"].macStyle & 0x02
    assert t["hhea"].caretSlopeRun > 0
    assert t["name"].getDebugName(2) == "Italic"


def test_italic_is_off_without_rules():
    font = load_font(ROOT / "examples/test_font/font.py")
    cf = compile_font(font, italic=True)      # no font.italic: unchanged
    assert cf.style == "Regular" and cf.italic_angle == 0
