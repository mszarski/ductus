#!/bin/bash
# ov.sh GLYPHS [FONT_PY] : overlay grid, ours vs Geist Sans, -> $DUCTUS_SCRATCH/ov.png
# GLYPHS is comma-separated glyph names (e.g. at,g,seven); FONT_PY defaults to examples/sans/font.py.
T=$(cd "$(dirname "$0")" && pwd); R=$(cd "$T/../.." && pwd); S=${DUCTUS_SCRATCH:-$T/_scratch}; mkdir -p "$S"
F=$(realpath "${2:-$R/examples/sans/font.py}")
cd "$R" && rm -rf "$S/ov_docs"
python -m ductus.cli bench "$F" --reference benchmarks/geist_sans/reference/Geist-Regular.woff2 --docs "$S/ov_docs" --iteration 1 --glyphs "$1" >/dev/null 2>&1 || { echo "bench failed"; exit 1; }
python - "$S" <<'PY'
import sys, glob
from PIL import Image
S = sys.argv[1]
ims = [Image.open(f) for f in sorted(glob.glob(f"{S}/ov_docs/iterations/01/*.png"))]
w = max(i.width for i in ims); h = max(i.height for i in ims); cols = min(6, len(ims)); rows = (len(ims) + cols - 1) // cols
out = Image.new("RGB", (w * cols, h * rows), "white")
for k, i in enumerate(ims):
    out.paste(i, ((k % cols) * w, (k // cols) * h))
out.save(f"{S}/ov.png"); print(f"{S}/ov.png")
PY
