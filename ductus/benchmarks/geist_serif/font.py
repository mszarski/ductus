"""INTERNAL BENCHMARK ONLY -- never build or release this font.

The serif kit with parameter values tuned by `ductus fit` (saved in
fitted.yaml) to measure how well the language represents Geist Serif.
Fitted values derive from the reference, so this stays in benchmarks/.
"""
from pathlib import Path

import yaml

from ductus import Font
from ductus.kits import serif as kit

font = Font("Ductus Bench Serif", upm=1000)

fitted = yaml.safe_load((Path(__file__).parent / "fitted.yaml").read_text()) or {}
P = kit.params(**fitted)
# the benchmark's original core set (docs/representability.md reports it); since round 7 of
# docs/sans/README.md the benchmark defines the kit's whole glyph set, fitted glyph by glyph
CORE = "onHeasgvhmburfti"
kit.define(font, P, terminals=kit.bracketed_set(P), g_ear="flag", g_band="flat", b_style="lobe", G_jaw="serif",
           E_serifs="wedge", ced_style="tick")
