# compattest.py [k ...] : how many sans glyphs the compatibilizer unifies across Regular and weight masters
import sys, time
from fitpaths import FONT
from ductus.loader import load_font; from ductus.compile import compile_font
from ductus.kits.serif import weight_master
from ductus import compat
ks = [float(x) for x in (sys.argv[1:] or ["0.7", "1.45"])]
f = load_font(str(FONT)); reg = compile_font(f)
ms_all = [reg] + [compile_font(f, weight_master(reg.params, k)) for k in ks]
t = time.time(); ok = 0; bad = []
for n in reg.glyphs:
    ms = [cf.glyphs[n].contours for cf in ms_all]
    r = compat.compatible(ms)
    if r is None:
        bad.append(f"{n}[{compat.LAST_FAIL}]"); continue
    assert len({tuple(c.signature() for c in m) for m in r}) == 1, n
    for m0, m1 in zip(ms, r):
        assert abs(sum(c.area() for c in m0) - sum(c.area() for c in m1)) < 1, n
    ok += 1
print(f"compatible {ok} of {len(reg.glyphs)} ({time.time() - t:.1f}s); failed: {' '.join(bad)}")
