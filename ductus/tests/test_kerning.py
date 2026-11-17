"""The optical kerner's style weights and their saturation (display serif iteration 36)."""
import json
from pathlib import Path

import pytest

from ductus.compile import compile_font
from ductus.kerning import Kerner
from ductus.loader import load_font

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def glyphs():
    f = load_font(ROOT / "examples/display_serif/font.py")
    f.kerning = {}
    return compile_font(f, glyphs=list("ALTVHnoa") + ["quotedblleft"]).glyphs


def test_saturate_off_is_the_plain_style(glyphs):
    w = {"L": [0.5, 1.0], "T": [1.0, 0.5]}
    plain = Kerner(glyphs, strength=0.6, clearance=90, weights=w)
    off = Kerner(glyphs, strength=0.6, clearance=90, weights=w, saturate=0)
    for a, b in [("L", "T"), ("A", "V"), ("H", "n"), ("o", "a")]:
        assert plain.kern(a, b) == off.kern(a, b)
        assert off.style_share(a, b) == 1.0


def test_saturate_lets_a_large_pair_escape_its_weights(glyphs):
    # LT is a large optical difference (the T's bar over the L's arm): weights 0.5 x 0.5 would quarter it
    w = {"L": [0.5, 1.0], "T": [1.0, 0.5]}
    raw = Kerner(glyphs, strength=0.6, clearance=90).kern("L", "T")
    styled = Kerner(glyphs, strength=0.6, clearance=90, weights=w).kern("L", "T")
    sat = Kerner(glyphs, strength=0.6, clearance=90, weights=w, saturate=150)
    assert raw < -80 and abs(styled) < abs(raw) / 2
    assert sat.style_share("L", "T") < 0.3
    assert abs(sat.kern("L", "T")) > abs(styled) + 30
    # a pair with little to correct keeps nearly all of its style
    assert sat.style_share("H", "n") > 0.8


def test_the_display_serif_kerning_records_its_settings():
    d = json.loads((ROOT / "examples/display_serif/kerning.json").read_text())
    assert d["settings"]["saturate"] == 150
    pairs = {(a, b): v for a, b, v in d["pairs"]}
    assert pairs[("L", "T")] <= -90 and pairs[("A", "V")] >= -150
