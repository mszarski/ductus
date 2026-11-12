"""The browser editor's Python side (web/driver.py), run here in CPython.

In the browser it runs in Pyodide with Paper.js doing the booleans; here it
runs on the example faces copied to a temp folder, once with skia-pathops and
once through the Paper.js adapter's glue (the stand-in backend of
test_pathops_js.py), and must hand back a loadable .otf of just the text's
glyphs.
"""
import importlib.util
import io
import json
import shutil
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def driver(tmp_path):
    for face in ("sans", "display_serif"):
        shutil.copytree(ROOT / "examples" / face, tmp_path / face)
    spec = importlib.util.spec_from_file_location("ductus_web_driver", ROOT / "web/driver.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.EXAMPLES = tmp_path
    mod.FACES = {"sans": tmp_path / "sans/font.py", "display": tmp_path / "display_serif/font.py"}
    return mod


def test_describe(driver):
    sans = json.loads(driver.describe("sans"))
    assert sans["axis"] == "wght" and sans["masters"] == [300, 400, 700] and sans["italic"]
    disp = json.loads(driver.describe("display"))
    assert disp["axis"] == "opsz" and disp["masters"] == [9, 72]


@pytest.mark.parametrize("face,master,italic", [("sans", 400, False), ("sans", 700, True),
                                                ("display", 72, False), ("display", 9, False)])
def test_build_returns_the_texts_glyphs(driver, face, master, italic):
    otf, ms, n = driver.build(face, json.dumps({}), "Hamburg é!", italic, master)
    t = TTFont(io.BytesIO(otf))
    cmap = t.getBestCmap()
    assert all(ord(c) in cmap for c in "Hamburg é!")
    assert n < 40                                  # only what the text needs (+ bases of composites)
    if italic:
        assert t["post"].italicAngle < 0


def test_build_through_the_paper_adapter(driver, monkeypatch):
    from ductus import _pathops_js as pj
    from ductus import compile as comp
    spec = importlib.util.spec_from_file_location("ductus_test_pathops_js", Path(__file__).with_name("test_pathops_js.py"))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    _fake_paper = helper._fake_paper
    monkeypatch.setattr(comp, "pathops", pj)
    pj.set_backend(_fake_paper)
    try:
        otf, ms, n = driver.build("sans", json.dumps({"400": {"stem": 100}}), "oe", False, 400)
    finally:
        pj.set_backend(None)
    t = TTFont(io.BytesIO(otf))
    assert {ord("o"), ord("e")} <= set(t.getBestCmap())


def test_master_values_are_the_masters_own(driver):
    reg = json.loads(driver.master_values("sans", "{}", 400))
    bold = json.loads(driver.master_values("sans", "{}", 700))
    assert reg["stem"][0] == 84
    assert bold["stem"][0] > 140                       # the Bold's real stem, not the Regular's
    lo, hi = bold["stem"][1]
    assert lo <= bold["stem"][0] <= hi                 # the slider range holds it
    # a value set at the Bold replaces the Bold's own, and leaves the Regular alone
    state = json.dumps({"700": {"stem": 170}})
    assert json.loads(driver.master_values("sans", state, 700))["stem"][0] == 170
    assert json.loads(driver.master_values("sans", state, 400))["stem"][0] == 84
    # a Regular change carries to the Bold where the Bold only scales it
    text = json.loads(driver.master_values("display", json.dumps({"72": {"hairline": 40}}), 9))
    assert text["hairline"][0] == pytest.approx(40 * 1.6)


def _stem_width(otf, ch="l"):
    from fontTools.pens.boundsPen import BoundsPen
    t = TTFont(io.BytesIO(otf))
    gs = t.getGlyphSet()
    bp = BoundsPen(gs)
    gs[t.getBestCmap()[ord(ch)]].draw(bp)
    return bp.bounds[2] - bp.bounds[0]


def test_a_masters_slider_changes_only_that_master(driver):
    state = json.dumps({"700": {"cap_stem": 200}})
    bold0, _, _ = driver.build("sans", "{}", "I", False, 700)
    bold1, _, _ = driver.build("sans", state, "I", False, 700)
    reg0, _, _ = driver.build("sans", "{}", "I", False, 400)
    reg1, _, _ = driver.build("sans", state, "I", False, 400)
    assert _stem_width(bold1, "I") == pytest.approx(200, abs=1)
    assert _stem_width(bold1, "I") > _stem_width(bold0, "I")
    assert _stem_width(reg1, "I") == _stem_width(reg0, "I")


def test_glyph_view_and_dragged_points(driver):
    g = json.loads(driver.glyph("sans", "{}", "n", 400))
    nodes = {n["name"]: n for s in g["skeleton"] for n in s["nodes"]}
    assert g["name"] == "n" and "n.arch.shoulder" in nodes and g["svg"].startswith("M")
    ov = json.dumps({"n.arch.shoulder": {"dx": 30, "dy": -20}})
    g2 = json.loads(driver.glyph("sans", "{}", "n", 400, ov))
    moved = {n["name"]: n for s in g2["skeleton"] for n in s["nodes"]}["n.arch.shoulder"]
    assert moved["x"] == pytest.approx(nodes["n.arch.shoulder"]["x"] + 30, abs=0.01)
    assert moved["y"] == pytest.approx(nodes["n.arch.shoulder"]["y"] - 20, abs=0.01)
    assert g2["svg"] != g["svg"]
    # the override reaches the built font, at another master too
    a, _, _ = driver.build("sans", "{}", "n", False, 700)
    b, _, _ = driver.build("sans", "{}", "n", False, 700, ov)
    assert a != b
    # an accented letter shows its base's points
    # a glyph built from shapes has no skeleton: its outline points are dragged (stage: outline),
    # and an accented letter shows its base's
    e = json.loads(driver.glyph("sans", "{}", "é", 400))
    assert e["name"] == "eacute" and "e.bar.bl" in e["outline_points"]
    ov = json.dumps({"e.bar.bl": {"dx": 0, "dy": -30, "stage": "outline"}})
    e2 = json.loads(driver.glyph("sans", "{}", "e", 400, ov))
    assert e2["outline_points"]["e.bar.bl"][1] == pytest.approx(e["outline_points"]["e.bar.bl"][1] - 30, abs=0.01)
    assert e2["svg"] != json.loads(driver.glyph("sans", "{}", "e", 400))["svg"]
    assert "error" in json.loads(driver.glyph("sans", "{}", "\u4e00", 400))
