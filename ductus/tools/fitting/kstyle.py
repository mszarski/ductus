# kstyle.py [lam_w] [lam_b] : fit per-glyph kerning style to Geist Sans's kerning -> SCRATCH/kern_weights.json
# Each glyph gets [weight as left, weight as right, bias as left, bias as right]: the pair's kern is
# our optical correction x both weights + both biases (see ductus.kerning.Kerner). Alternating least
# squares; weights regularised toward 1 (lam_w), biases toward 0 (lam_b; 20 did best on held-out pairs).
import sys, json, numpy as np
from fitpaths import FONT, SCRATCH
from ductus.loader import load_font; from ductus.compile import compile_font
from ductus.kerning import Kerner
from fontTools.agl import UV2AGL
d = json.load(open(str(SCRATCH) + '/geist_kern.json')); pairs = [tuple(p) for p in d["pairs"]]; gk = np.array(d["gk"])
f = load_font(str(FONT)); f.kerning = {}
cf = compile_font(f)
nm = lambda c: c if c.isascii() and c.isalpha() else UV2AGL.get(ord(c))
keep = [i for i, (a, b) in enumerate(pairs) if a.isalpha() or b.isalpha()]       # no punct-punct
P = [(nm(pairs[i][0]), nm(pairs[i][1])) for i in keep]; G = gk[keep]
kr = Kerner(cf.glyphs, strength=0.6, punct_strength=0.3, clearance=60)
R = np.array([kr.correction(a, b) for a, b in P])
names = sorted({x for p in P for x in p}); ix = {n: i for i, n in enumerate(names)}; n = len(names)
L = np.array([ix[a] for a, _ in P]); Rr = np.array([ix[b] for _, b in P])
lam = float(sys.argv[1]) if len(sys.argv) > 1 else 2000.0
lamb = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
wl = np.ones(n); wr = np.ones(n); bl = np.zeros(n); br = np.zeros(n)
for it in range(40):
    for (w, other, own, oth) in ((wl, wr, L, Rr), (wr, wl, Rr, L)):
        x = R * other[oth]; tgt = G - (bl[L] + br[Rr])
        w[:] = np.clip((np.bincount(own, x * tgt, n) + lam) / (np.bincount(own, x * x, n) + lam), 0.0, 2.5)
    res = G - R * wl[L] * wr[Rr]
    bl[:] = np.bincount(L, res - br[Rr], n) / (np.bincount(L, minlength=n) + lamb)
    br[:] = np.bincount(Rr, res - bl[L], n) / (np.bincount(Rr, minlength=n) + lamb)
fit = R * wl[L] * wr[Rr] + bl[L] + br[Rr]
print("fit MAE (raw, no clearance)", round(np.mean(np.abs(fit - G)), 1), "corr", round(np.corrcoef(fit, G)[0, 1], 3))
W = {nme: [round(float(wl[i]), 2), round(float(wr[i]), 2), round(float(bl[i]), 1), round(float(br[i]), 1)]
     for nme, i in ix.items()}
json.dump(W, open(str(SCRATCH) + '/kern_weights.json', 'w'), indent=0)
print({k: W[k] for k in ["T", "r", "x", "f", "L", "A", "V", "period"] if k in W})
