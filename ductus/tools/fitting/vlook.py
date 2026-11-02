# vlook.py TEXT out.png SIZE "k=v,k=v" ["k=v" ...] : Geist Sans, then the current font, then each
# parameter variant, one row each (scratch only). Variants edit kit.params(...) values in a temp copy.
import re, sys, uuid
from fitpaths import FONT, SCRATCH, SW, geist_otf
from PIL import Image, ImageDraw
from ductus.loader import load_font; from ductus.compile import compile_font; from ductus.emit import build_otf; from ductus.proof import render_text
text, out, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
src = open(FONT).read()
rows = [("Geist Sans", geist_otf())]
for var in [""] + sys.argv[4:]:
    s = src
    for kv in filter(None, var.split(",")):
        k, v = kv.split("=")
        s = re.sub(rf"\b{k}=[-0-9.]+", f"{k}={v}", s, count=1) if re.search(rf"\b{k}=", s) else s.replace("P = kit.params(", f"P = kit.params({k}={v},", 1)
    fn = SW / f"_v{uuid.uuid4().hex[:6]}.py"; fn.write_text(s)
    rows.append((var or "current", build_otf(compile_font(load_font(str(fn))), SW / f"{fn.stem}.otf")))
ims = []
for label, f in rows:
    im = Image.open(render_text(f, text, SCRATCH / "_vl.png", size=size)).convert("L")
    ImageDraw.Draw(im).text((4, 2), label, fill=0)
    ims.append(im)
W = max(i.width for i in ims); img = Image.new("L", (W, sum(i.height for i in ims)), 255); y = 0
for i in ims:
    img.paste(i, (0, y)); y += i.height
img.save(out)
