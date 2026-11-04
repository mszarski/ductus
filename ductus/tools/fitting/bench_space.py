# bench_space.py : fit the Geist Serif benchmark's side bearings to the reference's (benchmark only, never released)
#   python tools/fitting/bench_space.py      -> benchmarks/geist_serif/spacing.json
# For every non-composite glyph the reference has, deltas (dl, dr) make our left / right side bearings equal
# Geist Serif's; empty glyphs (space) take the reference's advance. Accented letters follow their base.
# Run twice if spacing.json existed (deltas add to the current ones); rerun `ductus kern` afterwards.
import json
from fitpaths import ROOT
from ductus.loader import load_font
from ductus.compile import compile_font
from ductus.bench.reference import Reference

FONT = ROOT / "benchmarks/geist_serif/font.py"
OUT = FONT.with_name("spacing.json")
font = load_font(str(FONT))
cf = compile_font(font)
ref = Reference(ROOT / "benchmarks/geist_serif/reference/GeistSerif-Regular.woff2")
comp = getattr(font, "composites", {})
cur = json.loads(OUT.read_text()) if OUT.exists() else {}
new, moved = {}, 0
for name, g in cf.glyphs.items():
    rn = ref.name_for(g.unicode, name)
    if rn is None or name in comp:
        if name in cur:
            new[name] = cur[name]
        continue
    rc, radv = ref.glyph(rn)
    dl0, dr0 = cur.get(name, (0, 0))
    if not g.contours or not rc:
        d = round(radv - g.advance)
        new[name] = [dl0 + d // 2, dr0 + d - d // 2]
        continue
    xs = [p[0] for c in rc for p in c.pts]
    rl, rr = min(xs), radv - max(xs)
    ol, orr = g.bounds[0], g.advance - g.bounds[2]
    dl, dr = round(rl - ol), round(rr - orr)
    moved += abs(dl) + abs(dr) > 1
    new[name] = [dl0 + dl, dr0 + dr]
OUT.write_text(json.dumps(dict(sorted(new.items())), indent=0))
print(f"{len(new)} glyphs, {moved} moved -> {OUT}")
