# look.py "line§line" out.png [SIZE] [FONT_PY] : each line set in ours, then in Geist Sans (scratch only)
import sys
from fitpaths import FONT, SCRATCH, geist_otf
from PIL import Image
from ductus.loader import load_font; from ductus.compile import compile_font; from ductus.emit import build_otf; from ductus.proof import render_text
size = int(sys.argv[3]) if len(sys.argv) > 3 else 120
o = build_otf(compile_font(load_font(sys.argv[4] if len(sys.argv) > 4 else str(FONT))), SCRATCH / "look.otf")
ims = []
for t in sys.argv[1].split("§"):
    for k, f in enumerate((o, geist_otf())):
        ims.append(Image.open(render_text(f, t, SCRATCH / f"_l{k}.png", size=size)).convert("L"))
W = max(i.width for i in ims); out = Image.new("L", (W, sum(i.height for i in ims)), 255); y = 0
for i in ims:
    out.paste(i, (0, y)); y += i.height
out.save(sys.argv[2])
