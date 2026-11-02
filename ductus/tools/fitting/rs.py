# rs.py GLYPHS N p:scale ... : random joint search -- Gaussian steps on several params at once (scaled by
# `scale`, shrinking when stuck), keeping a candidate only if mean IoU over GLYPHS improves and lint (overlaps, direction, stems) stays clean.
# For moves one-at-a-time descent (cd2.py) can't make. Prints `end <iou> {changes}`; does not write the font.
import random, re, sys, uuid
from fitpaths import FONT, REF, SW
from ductus.loader import load_font; from ductus.compile import compile_font
from ductus.bench.reference import Reference; from ductus.bench.run import score_font
from ductus.kits.serif import DEFAULTS
from ductus.lint import check_self_intersections, check_direction, check_stems
from ductus.params import evaluating
ref = Reference(REF)
gl = [x for x in sys.argv[1].split(",") if x] if "," in sys.argv[1] else list(sys.argv[1])
N = int(sys.argv[2]); ps = [(a.split(":")[0], float(a.split(":")[1])) for a in sys.argv[3:]]
src = open(FONT).read()
def cur(k):
    m = re.search(rf"\b{k}=([-0-9.]+)", src)
    return float(m.group(1)) if m else float(DEFAULTS[k][0])
def score(ch):
    s = src
    for k, v in ch.items():
        s = re.sub(rf"\b{k}=[-0-9.]+", f"{k}={v}", s, count=1) if re.search(rf"\b{k}=", s) else s.replace("P = kit.params(", f"P = kit.params({k}={v},", 1)
    fn = SW / f"_r{uuid.uuid4().hex[:8]}.py"; fn.write_text(s)
    try:
        f = load_font(str(fn)); cf = compile_font(f, glyphs=gl)
        def exp(st):     # as lint: stems of profiled strokes or strokes with node dw are not checked
            if st.profile is not None or any(n.dw for n in st.nodes): return None
            return (st.pen or f.pen).width_at(90)
        with evaluating(cf.params):
            if any(x.level == "error" for g in gl for x in check_self_intersections(cf.glyphs[g])
                   + check_direction(cf.glyphs[g]) + check_stems(cf.glyphs[g], exp)):
                return -1
        sc = score_font(cf, ref, gl); return sum(x.iou for x in sc.values()) / len(sc)
    except Exception:
        return -1
B = {k: cur(k) for k, _ in ps}; best = score(B); print("start", round(best, 4), flush=True)
scale, stuck = 1.0, 0
random.seed(1)
for i in range(N):
    c = dict(B)
    for k, st in random.sample(ps, k=random.randint(2, min(4, len(ps)))):
        lo, hi = DEFAULTS[k][1]
        c[k] = round(min(hi, max(lo, c[k] + random.gauss(0, st * scale))), 4)
    s = score(c)
    if s > best + 1e-4:
        best, B, stuck = s, c, 0; print(i, round(best, 4), flush=True)
    else:
        stuck += 1
        if stuck > 25: scale, stuck = max(scale * 0.6, 0.15), 0
print("end", round(best, 4), {k: v for k, v in B.items() if v != cur(k)})
