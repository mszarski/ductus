"""Shared paths for the fitting scripts: the project from this file's location,
scratch output under $DUCTUS_SCRATCH (default: tools/fitting/_scratch, git-ignored)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]            # the ductus project dir (pyproject.toml)
sys.path.insert(0, str(ROOT))
FONT = ROOT / "examples/sans/font.py"
REF = ROOT / "benchmarks/geist_sans/reference/Geist-Regular.woff2"
SCRATCH = Path(os.environ.get("DUCTUS_SCRATCH", Path(__file__).resolve().parent / "_scratch"))
SW = SCRATCH / "sw"                                   # one temp font per evaluation
SW.mkdir(parents=True, exist_ok=True)


def geist_otf() -> str:
    """The reference as a plain .otf in scratch (for FreeType renders and GPOS reads)."""
    out = SCRATCH / "geist_sans.otf"
    if not out.exists():
        from fontTools.ttLib import TTFont
        f = TTFont(str(REF)); f.flavor = None; f.save(str(out))
    return str(out)
