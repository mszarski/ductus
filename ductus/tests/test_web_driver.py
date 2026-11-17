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


def test_a_move_at_one_master_only(driver):
    ov = json.dumps({"masters": {"700": {"n.arch.shoulder": {"dx": 40}}}})
    bold0 = json.loads(driver.glyph("sans", "{}", "n", 700))
    bold1 = json.loads(driver.glyph("sans", "{}", "n", 700, ov))
    reg0 = json.loads(driver.glyph("sans", "{}", "n", 400))
    reg1 = json.loads(driver.glyph("sans", "{}", "n", 400, ov))
    node = lambda g: {n["name"]: n for s in g["skeleton"] for n in s["nodes"]}["n.arch.shoulder"]
    assert node(bold1)["x"] == pytest.approx(node(bold0)["x"] + 40, abs=0.01)
    assert reg1["svg"] == reg0["svg"]
    # at the default master: in the preview there only, exported as a move for all with the
    # opposite move at the other masters
    ov = json.dumps({"masters": {"400": {"n.arch.shoulder": {"dx": 10}}}})
    assert json.loads(driver.glyph("sans", "{}", "n", 400, ov))["svg"] != reg0["svg"]
    assert json.loads(driver.glyph("sans", "{}", "n", 700, ov))["svg"] == bold0["svg"]
    files = json.loads(driver.export("sans", json.dumps({"700": {"stem": 150}}), ov))
    assert "n.arch.shoulder: { dx: 10" in files["overrides.yaml"]
    assert "n.arch.shoulder: { dx: -10" in files["overrides_700.yaml"]
    assert "n.arch.shoulder: { dx: -10" in files["overrides_300.yaml"]
    assert json.loads(files["params_700.json"]) == {"stem": 150}


def test_exported_master_files_are_read_by_the_face(driver, tmp_path):
    from ductus.loader import load_font
    from ductus.variable import compile_master
    ov = json.dumps({"masters": {"700": {"n.arch.shoulder": {"dx": 40}}}})
    for name, text in json.loads(driver.export("sans", "{}", ov)).items():
        (tmp_path / "sans" / name).write_text(text)
    f = load_font(tmp_path / "sans/font.py")
    from ductus.compile import compile_font
    reg = compile_font(f, glyphs=["n"])
    bold = compile_master(f, reg.params, f.variable["masters"][700], glyphs=["n"])
    want = json.loads(driver.glyph("sans", "{}", "n", 700, ov))["svg"]
    assert bold.glyphs["n"].to_json()["svg"] == want


def test_stroke_shape_and_handle_deltas(driver):
    g0 = json.loads(driver.glyph("sans", "{}", "n", 400))
    node0 = {n["name"]: n for s in g0["skeleton"] for n in s["nodes"]}["n.arch.shoulder"]
    ov = json.dumps({"all": {"n.arch.shoulder": {"dw": 12, "da": 5, "dt": 0.1}}})
    g1 = json.loads(driver.glyph("sans", "{}", "n", 400, ov))
    node1 = {n["name"]: n for s in g1["skeleton"] for n in s["nodes"]}["n.arch.shoulder"]
    assert node1["width"] > node0["width"] + 8              # dw blends into the stroke's width profile
    assert node1["dir"] == pytest.approx(node0["dir"] + 5, abs=0.01)
    assert g1["svg"] != g0["svg"]
    h = {x["param"]: x for x in g0["handles"]}
    assert "n_join_at" in h and h["n_join_at"]["per_unit"]
    g2 = json.loads(driver.glyph("sans", "{}", "n", 400, json.dumps({"n.@n_notch": {"dv": 8}})))
    assert {x["param"]: x for x in g2["handles"]}["n_notch"]["value"] == pytest.approx(h["n_notch"]["value"] + 8)
    assert g2["svg"] != g0["svg"]


@pytest.mark.parametrize("ch", ["n", "o", "e"])
def test_italic_glyph_view(driver, ch):
    from ductus.italic import apply
    up = json.loads(driver.glyph("sans", "{}", ch, 400))
    it = json.loads(driver.glyph("sans", "{}", ch, 400, "{}", True))
    assert it["italic_angle"] > 0 and it["svg"] != up["svg"]
    m, inv = it["matrix"], it["inverse"]
    # the view is the italic as built
    otf, _, _ = driver.build("sans", "{}", ch, True, 400)
    from fontTools.pens.boundsPen import BoundsPen
    t = TTFont(io.BytesIO(otf)); gs = t.getGlyphSet(); bp = BoundsPen(gs)
    gs[t.getBestCmap()[ord(ch)]].draw(bp)
    xs = [p for c in it["outline_points"].values() for p in c[:1]] or [0]
    assert bp.bounds[0] - 2 <= min(xs) and max(xs) <= bp.bounds[2] + 2
    # points are the upright's mapped; a move in the view maps back by the inverse
    for name, p in up["outline_points"].items():
        assert it["outline_points"][name] == pytest.approx(list(apply(m, *p)), abs=1e-6)
    dx, dy = 10.0, 20.0
    ux, uy = inv[0] * dx + inv[2] * dy, inv[1] * dx + inv[3] * dy
    assert (m[0] * ux + m[2] * uy, m[1] * ux + m[3] * uy) == pytest.approx((dx, dy))
