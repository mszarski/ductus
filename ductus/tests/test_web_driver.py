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
    assert "stem" in sans["params"]
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
        otf, ms, n = driver.build("sans", json.dumps({"stem": 100}), "oe", False, 400)
    finally:
        pj.set_backend(None)
    t = TTFont(io.BytesIO(otf))
    assert {ord("o"), ord("e")} <= set(t.getBestCmap())
