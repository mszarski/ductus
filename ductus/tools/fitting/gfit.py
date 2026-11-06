# gfit.py : fit one glyph's own parameters at one weight of Ductus Sans, scoring every glyph they touch
#   python tools/fitting/gfit.py 300|400|700 GLYPH N [prefix_or_param ...] [--dry] [--wide] [--bench]
# --composites: also score the accented glyphs the parameters touch (for marks, whose composites matter most).
# --bench: the Geist Serif benchmark (benchmarks/geist_serif, 400 only) instead of the sans; writes its fitted.yaml.
# Parameters: those starting with the given prefixes (default: "<glyph>_"), or exact names. Steps are 4% of
# each parameter's range; --wide (masters only) extends each range by its width on both sides, for
# offsets that should grow with the stem but are not weight parameters. Random joint search (N rounds, Gaussian moves on 1-4 parameters, shrinking scale).
# Objective, averaged over the glyphs those parameters change: IoU - 0.001 * Hausdorff (font units), so a
# local bump in the outline counts, not only overlap. Candidates must keep every touched glyph's contour
# count and stay free of self-intersection / direction errors.
# Writes: 700 / 300 -> examples/sans/master_bold.json / master_light.json. 400 -> examples/sans/font.py (via apply.py); before a
# Regular value changes, its current value at each weight master is pinned into that master's json, so a
# Regular fit never moves the Bold or the Light.
import json, random, subprocess, sys
from fitpaths import FONT, ROOT
from ductus.loader import load_font
from ductus.compile import compile_font
from ductus.variable import compile_master
from ductus.bench.reference import Reference
from ductus.bench.run import score_font
from ductus.kits.serif import DEFAULTS, WEIGHT_PARAMS
from ductus.lint import check_self_intersections, check_direction

args = sys.argv[1:]
dry, wide, bench, withc = "--dry" in args, "--wide" in args, "--bench" in args, "--composites" in args
for flag in ("--dry", "--wide", "--bench", "--composites"):
    if flag in args:
        args.remove(flag)
W, G, N = int(args[0]), args[1], int(args[2])
sel = args[3:] or [G + "_"]
if bench:
    # the Geist Serif benchmark: one weight, values in fitted.yaml (benchmark only, never released)
    FONT = ROOT / "benchmarks/geist_serif/font.py"
    assert W == 400, "the benchmark has one weight"
font = load_font(str(FONT))
d = compile_font(font)
MASTERS = {} if bench else {700: "bold", 300: "light"}
data = {loc: json.loads(FONT.with_name(f"master_{n}.json").read_text()) for loc, n in MASTERS.items()}
ref = Reference(ROOT / ("benchmarks/geist_serif/reference/GeistSerif-Regular.woff2" if bench else
                        f"benchmarks/geist_sans/reference/Geist-{ {300: 'Light', 400: 'Regular', 700: 'Bold'}[W] }.woff2"))


def setting(loc, extra):
    s = dict(font.variable["masters"][loc])
    s["params"] = {**data[loc].get("params", {}), **extra}
    s["spacing"] = data[loc].get("spacing", {})
    return s


def compile_at(extra, glyphs=None):
    if W == 400:
        return compile_font(font, extra, glyphs=glyphs)
    return compile_master(font, d.params, setting(W, extra), glyphs=glyphs)


base = compile_at({})
P0 = base.params
keys = sorted({k for k in DEFAULTS if any(k == s or (s.endswith("_") and k.startswith(s)) for s in sel)})
# set by eye to fix a visible fault (see docs/sans/README.md 11-18): a fit must not undo them
LOCKED = {"five_start_dy", "five_start_dir", "five_end_dir", "five_foot_dy", "three_end_dir", "nine_top_x",
          "nine_end_dir", "nine_root_dir", "nine_root_y", "nine_root_t", "nine_join_dfull", "six_join_dfull",
          "r_arch_dw", "a_bs_bias", "a_bl_dw", "a_bl_x", "a_bs_t", "sans_cut_fig", "sans_cut_fig_low",
          "n_leg_top", "u_leg_top", "n_shoulder_x", "ced_neck_dir"}
keys = [k for k in keys if not k.endswith(("_style", "_free")) and (k not in LOCKED or k in sel or bench)]
if not keys:
    sys.exit(f"no parameters for {sel}")
lo_hi = {}
for k in keys:
    lo, hi = DEFAULTS[k][1]
    if k in WEIGHT_PARAMS and W != 400:
        lo, hi = lo * 0.5, hi * 2.2
    elif wide and W != 400:
        lo, hi = lo - (hi - lo), hi + (hi - lo)
    lo_hi[k] = (lo, hi)
step = {k: (lo_hi[k][1] - lo_hi[k][0]) * 0.04 for k in keys}

# the glyphs these parameters touch: compile with all of them nudged and see what moved
nudged = compile_at({k: min(lo_hi[k][1], max(lo_hi[k][0], float(P0[k]) + step[k] * 0.5)) for k in keys})
def shape(g):
    return (len(g.contours), tuple(round(c.area(), 1) for c in g.contours), tuple(round(v, 1) for v in g.bounds))


touched = [n for n, g in base.glyphs.items()
           if g.contours and n in nudged.glyphs and shape(g) != shape(nudged.glyphs[n])]
scored = [n for n in touched if ref.name_for(base.glyphs[n].unicode, n)
          and (withc or n not in getattr(font, "composites", {}))] or [G]
ncont = {n: len(base.glyphs[n].contours) for n in touched}


def clusters(g):
    """On-curve points within 8 units of another on the same contour: how folds and kinks show."""
    import numpy as np
    k = 0
    for c in g.contours:
        on = np.array([p for p, t in zip(c.pts, c.types) if t == "on"])
        if len(on) > 1:
            dd = np.linalg.norm(on[:, None] - on[None], axis=2) + np.eye(len(on)) * 1e9
            k += int((dd.min(axis=1) < 8).sum())
    return k


nclus = {n: clusters(base.glyphs[n]) for n in touched}


def objective(extra):
    try:
        cf = compile_at(extra, glyphs=touched or [G])
        for n in touched:
            g = cf.glyphs[n]
            if len(g.contours) != ncont[n] or clusters(g) > nclus[n]:
                return None
            if any(x.level == "error" for x in check_self_intersections(g) + check_direction(g)):
                return None
        sc = score_font(cf, ref, scored)
        return sum(s.iou - 0.001 * s.hausdorff for s in sc.values()) / len(sc), sc
    except Exception:
        return None


B = {k: float(P0[k]) for k in keys}
r0 = objective(B)
if r0 is None:
    sys.exit(f"{G}: the current values fail the checks")
best, sc0 = r0
print(f"{G} @{W}: {len(keys)} params, scoring {len(scored)} glyphs: {' '.join(scored[:12])}{' ...' if len(scored) > 12 else ''}")
print(f"start {best:.4f}")
random.seed(1)
scale, stuck, scb = 1.0, 0, sc0
for i in range(N):
    c = dict(B)
    for k in random.sample(keys, k=random.randint(1, min(4, len(keys)))):
        lo, hi = lo_hi[k]
        c[k] = round(min(hi, max(lo, c[k] + random.gauss(0, step[k] * scale))), 3)
    r = objective(c)
    if r and r[0] > best + 1e-4:
        best, B, scb, stuck = r[0], c, r[1], 0
    else:
        stuck += 1
        if stuck > 20:
            scale, stuck = max(scale * 0.6, 0.1), 0
ch = {k: v for k, v in B.items() if abs(v - float(P0[k])) > 1e-9}
print(f"end {best:.4f} {json.dumps(ch)}")
print(f"old {json.dumps({k: float(P0[k]) for k in ch})}")
for n in scored:
    a, b = sc0[n], scb[n]
    if abs(a.iou - b.iou) > 1e-4 or abs(a.hausdorff - b.hausdorff) > 0.5:
        print(f"  {n}: IoU {a.iou:.3f} -> {b.iou:.3f}, Hausdorff {a.hausdorff:.0f} -> {b.hausdorff:.0f}")
if dry or not ch:
    sys.exit(0)
if W in MASTERS:
    data[W].setdefault("params", {}).update({k: round(v, 3) for k, v in ch.items()})
    FONT.with_name(f"master_{MASTERS[W]}.json").write_text(json.dumps(data[W], indent=1, sort_keys=True))
elif bench:
    import yaml
    fy = FONT.with_name("fitted.yaml")
    fitted = yaml.safe_load(fy.read_text()) or {}
    fitted.update({k: round(float(v), 4) for k, v in ch.items()})
    fy.write_text(yaml.safe_dump(dict(sorted(fitted.items())), sort_keys=True))
else:
    # pin each master's current value of every changed parameter, then write the Regular
    for loc, name in MASTERS.items():
        ov = font.variable["params"](d.params, setting(loc, {}))
        pins = {k: round(float(ov.get(k, P0[k])), 3) for k in ch if k not in data[loc].get("params", {})}
        if pins:
            data[loc].setdefault("params", {}).update(pins)
            FONT.with_name(f"master_{name}.json").write_text(json.dumps(data[loc], indent=1, sort_keys=True))
    subprocess.run([sys.executable, str(ROOT / "tools/fitting/apply.py"),
                    repr({k: round(v, 3) for k, v in ch.items()})], check=True, cwd=ROOT / "tools/fitting")
print("saved")
