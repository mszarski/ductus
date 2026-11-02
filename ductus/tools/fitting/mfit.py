# mfit.py : fit a weight master of the sans to the matching Geist weight; results go to master_<name>.json
#   python tools/fitting/mfit.py score [--loc 700]                     mean IoU of the master, weakest glyphs
#   python tools/fitting/mfit.py cd GLYPHS p:step ... [--loc 700]      coordinate descent, applied to the json
#   python tools/fitting/mfit.py rs GLYPHS N p:scale ... [--loc 700]   random joint search (lint-aware), applied
#   python tools/fitting/mfit.py respace [--loc 700]                   master side bearings toward the reference's
# GLYPHS as cd2.py: a string of single letters, or comma-separated names. A master's params start from
# kit.weight_master (thicknesses scaled) and the json's designed values replace them. Thickness ranges are widened
# (a bold's stems are beyond the regular's ranges). Candidates must keep each glyph's contour count (its topology).
import json, random, sys
from pathlib import Path
from fitpaths import FONT, ROOT, SCRATCH
from ductus.loader import load_font; from ductus.compile import compile_font
from ductus.bench.reference import Reference; from ductus.bench.run import score_font
from ductus.kits.serif import DEFAULTS, WEIGHT_PARAMS
from ductus.lint import check_self_intersections, check_direction
from ductus.variable import compile_master
from ductus.emit import build_otf

args = sys.argv[1:]
loc = 700
if "--loc" in args:
    i = args.index("--loc"); loc = int(args[i + 1]); del args[i:i + 2]
NAMES = {700: "bold", 300: "light"}
JSON = FONT.with_name(f"master_{NAMES[loc]}.json")
REF = ROOT / f"benchmarks/geist_sans/reference/Geist-{NAMES[loc].capitalize()}.woff2"
font = load_font(str(FONT)); default = compile_font(font)
setting = dict(font.variable["masters"][loc])
data = json.loads(JSON.read_text()) if JSON.exists() else {"params": {}, "spacing": {}}
ref = Reference(REF)


def master_params(extra):
    s = dict(setting); s["params"] = {**data.get("params", {}), **extra}
    s["spacing"] = data.get("spacing", {})
    return s


def current(k):
    if k in data.get("params", {}):
        return float(data["params"][k])
    ov = font.variable["params"](default.params, master_params({}))
    return float(ov[k]) if k in ov else float(default.params[k])


def bounds(k):
    lo, hi = DEFAULTS[k][1] if k in DEFAULTS else (-1e9, 1e9)
    if k in WEIGHT_PARAMS:
        lo, hi = lo * 0.5, hi * 2.2
    return lo, hi


def score(extra, gl):
    try:
        cf = compile_master(font, default.params, master_params(extra), glyphs=gl)
        if any(x.level == "error" for g in gl for x in check_self_intersections(cf.glyphs[g]) + check_direction(cf.glyphs[g])):
            return -1
        # a master must keep the regular's topology (a variable font interpolates them)
        if any(len(cf.glyphs[g].contours) != len(default.glyphs[g].contours) for g in gl):
            return -1
        sc = score_font(cf, ref, [g for g in gl if ref.name_for(cf.glyphs[g].unicode, g)])
        return sum(x.iou for x in sc.values()) / max(len(sc), 1)
    except Exception:
        return -1


def save(ch):
    data.setdefault("params", {}).update({k: round(v, 3) for k, v in ch.items()})
    JSON.write_text(json.dumps(data, indent=1, sort_keys=True))


def glyphs_of(a):
    return [x for x in a.split(",") if x] if "," in a else list(a)


cmd = args[0]
if cmd == "score":
    cf = compile_master(font, default.params, master_params({}))
    names = [n for n, g in cf.glyphs.items() if g.contours and ref.name_for(g.unicode, n)]
    sc = score_font(cf, ref, names)
    worst = sorted(sc.items(), key=lambda kv: kv[1].iou)[:20]
    print(f"{NAMES[loc]} MEAN IoU {sum(s.iou for s in sc.values()) / len(sc):.4f}  "
          + " ".join(f"{g}:{s.iou:.2f}" for g, s in worst))
elif cmd == "cd":
    gl = glyphs_of(args[1]); ps = [(a.split(":")[0], float(a.split(":")[1])) for a in args[2:]]
    B = {}; best = score(B, gl); print("start", round(best, 4))
    for rnd in range(3):
        imp = False
        for k, st in ps:
            for sg in (1, -1):
                while True:
                    lo, hi = bounds(k)
                    v = round(B.get(k, current(k)) + sg * st, 3)
                    if not lo <= v <= hi:
                        break
                    s = score({**B, k: v}, gl)
                    if s > best + 1e-4:
                        best, B[k], imp = s, v, True
                    else:
                        break
        if not imp:
            break
    print("end", round(best, 4), B); save(B)
elif cmd == "rs":
    gl = glyphs_of(args[1]); N = int(args[2]); ps = [(a.split(":")[0], float(a.split(":")[1])) for a in args[3:]]
    B = {k: current(k) for k, _ in ps}; best = score(B, gl); print("start", round(best, 4))
    scale, stuck = 1.0, 0; random.seed(1)
    for i in range(N):
        c = dict(B)
        for k, st in random.sample(ps, k=random.randint(1, min(4, len(ps)))):
            lo, hi = bounds(k)
            c[k] = round(min(hi, max(lo, c[k] + random.gauss(0, st * scale))), 3)
        s = score(c, gl)
        if s > best + 1e-4:
            best, B, stuck = s, c, 0
        else:
            stuck += 1
            if stuck > 25:
                scale, stuck = max(scale * 0.6, 0.15), 0
    ch = {k: v for k, v in B.items() if abs(v - current(k)) > 1e-9}
    print("end", round(best, 4), ch); save(ch)
elif cmd == "respace":
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    cf = compile_master(font, default.params, master_params({}))
    otf = build_otf(cf, SCRATCH / f"m{loc}.otf")

    def sbs(path):
        t = TTFont(str(path)); gs = t.getGlyphSet(); cm = t.getBestCmap(); out = {}
        for u, g in cm.items():
            p = BoundsPen(gs); gs[g].draw(p)
            if p.bounds:
                out[u] = (p.bounds[0], gs[g].width - p.bounds[2])
        return out
    a, b = sbs(otf), sbs(str(REF).replace(".woff2", ".woff2"))
    sp = data.setdefault("spacing", {}); n = 0
    for name, g in cf.glyphs.items():
        u = g.unicode
        if u is None or u not in a or u not in b or name in getattr(font, "composites", {}):
            continue
        dl, dr = round((b[u][0] - a[u][0]) / 2) * 2, round((b[u][1] - a[u][1]) / 2) * 2
        if abs(dl) < 2 and abs(dr) < 2:
            continue
        l0, r0 = sp.get(name, (0, 0)); sp[name] = (l0 + dl, r0 + dr); n += 1
    JSON.write_text(json.dumps(data, indent=1, sort_keys=True)); print("respaced", n)
