# weightprobe.py [k ...] : compile the sans with every stroke-thickness param scaled by k; report per glyph
# whether the merged outline -- or else the un-merged pieces -- keeps the regular's structure (what a variable
# font needs), and lint errors at that weight
import sys
from fitpaths import FONT
from ductus.loader import load_font; from ductus.compile import compile_font
from ductus.lint import check_self_intersections, check_direction
from ductus.kits.serif import weight_master
f = load_font(str(FONT)); base = compile_font(f, pieces=True)
for k in [float(x) for x in (sys.argv[1:] or ["0.7", "1.45"])]:
    cf = compile_font(f, weight_master(base.params, k), pieces=True)
    merged = [n for n, g in cf.glyphs.items() if g.signature != base.glyphs[n].signature]
    neither = [n for n in merged if cf.glyphs[n].piece_signature != base.glyphs[n].piece_signature]
    errs = sorted({n for n, g in cf.glyphs.items()
                   for x in check_self_intersections(g) + check_direction(g) if x.level == "error"})
    print(f"k={k}: merged differs in {len(merged)}/{len(cf.glyphs)}; of those, pieces differ too in {len(neither)}: "
          f"{' '.join(neither)}; lint errors: {' '.join(errs) or 'none'}")
