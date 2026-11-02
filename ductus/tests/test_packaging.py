"""Every subpackage of ductus must ship in a regular (non-editable) install."""
from pathlib import Path

import tomllib
from setuptools import find_packages

ROOT = Path(__file__).resolve().parents[1]


def test_every_subpackage_is_packaged():
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["setuptools"]
    include = cfg["packages"]["find"]["include"]
    shipped = set(find_packages(str(ROOT), include=include))
    on_disk = {".".join(p.parent.relative_to(ROOT).parts) for p in (ROOT / "ductus").rglob("__init__.py")}
    assert on_disk <= shipped, sorted(on_disk - shipped)
    assert "ductus.kits" in shipped
