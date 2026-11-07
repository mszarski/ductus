"""Write a static CFF-flavoured .otf with fontTools.fontBuilder."""
from __future__ import annotations

import re
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen

from .compile import CompiledFont


def ps_name(cf: CompiledFont) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", cf.family) + "-" + re.sub(r"[^A-Za-z0-9]", "", cf.style)


def build_otf(cf: CompiledFont, path, optimize: bool = True):
    """Write to ``path`` (str/Path) or a binary file object. ``optimize=False``
    keeps every segment's command as drawn (the charstring optimiser turns
    straight curves into lines, which differs between variable masters)."""
    if isinstance(path, (str, Path)):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
    m = {k: round(v) for k, v in cf.metrics.items()}
    upm = cf.upm
    order = [".notdef"] + list(cf.glyphs)
    fb = FontBuilder(upm, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({g.unicode: g.name for g in cf.glyphs.values() if g.unicode is not None})

    charstrings, metrics = {}, {}
    # .notdef: an open box
    nd_w = round(upm * 0.5)
    pen = T2CharStringPen(nd_w, None)
    t = 50
    for x0, y0, x1, y1, cw in ((50, 0, nd_w - 50, m["capheight"], False),
                              (50 + t, t, nd_w - 50 - t, m["capheight"] - t, True)):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        if cw:
            pts = pts[::-1]
        pen.moveTo(pts[0]); [pen.lineTo(p) for p in pts[1:]]; pen.closePath()
    charstrings[".notdef"] = pen.getCharString()
    metrics[".notdef"] = (nd_w, 50)
    for g in cf.glyphs.values():
        pen = T2CharStringPen(g.advance, None)
        for c in g.contours:
            c.draw(pen)
        charstrings[g.name] = pen.getCharString(optimize=optimize)
        metrics[g.name] = (g.advance, int(round(g.bounds[0])) if g.bounds else 0)

    fb.setupCFF(ps_name(cf), {"FullName": f"{cf.family} {cf.style}", "FamilyName": cf.family,
                              "Weight": cf.style}, charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    asc, desc = m["ascender"], m["descender"]
    ia = float(getattr(cf, "italic_angle", 0.0) or 0.0)
    if ia:      # the caret follows the slant
        import math as _m
        fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0, caretSlopeRise=1000,
                                 caretSlopeRun=round(1000 * _m.tan(_m.radians(-ia))))
    else:
        fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0)
    fb.setupNameTable({"familyName": cf.family, "styleName": cf.style,
                       "uniqueFontIdentifier": f"Ductus;{ps_name(cf)}",
                       "fullName": f"{cf.family} {cf.style}", "psName": ps_name(cf),
                       "version": "Version 0.001"})
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
                usWinAscent=max(asc, 0) + 20, usWinDescent=abs(desc) + 20,
                sxHeight=m["xheight"], sCapHeight=m["capheight"], achVendID="NONE",
                fsType=0, fsSelection=((0x01 if ia else 0) | (0x20 if "Bold" in cf.style else 0)) or 0x40)
    fb.setupPost(italicAngle=ia)
    from fontTools.misc.timeTools import timestampNow
    now = timestampNow()
    fb.setupHead(unitsPerEm=upm, created=now, modified=now,
                 macStyle=(0x02 if ia else 0) | (0x01 if "Bold" in cf.style else 0))
    kerning = getattr(cf, "kerning", None) or {}
    ligatures = getattr(cf, "ligatures", None) or {}
    fea = ""
    if ligatures:
        # GSUB standard ligatures (longest first, as feature files expect)
        fea += "feature liga {\n" + "".join(
            f"  sub {' '.join(comps)} by {lg};\n"
            for lg, comps in sorted(ligatures.items(), key=lambda kv: -len(kv[1]))) + "} liga;\n"
    if kerning:
        # GPOS pair kerning (what applications use) ...
        fea += "feature kern {\n" + "".join(
            f"  pos {a} {b} {v};\n" for (a, b), v in sorted(kerning.items())) + "} kern;\n"
    if fea:
        fb.addOpenTypeFeatures(fea)
    if kerning:
        # ... and a legacy 'kern' table, which FreeType's proofs read directly
        from fontTools.ttLib import newTable
        from fontTools.ttLib.tables._k_e_r_n import KernTable_format_0
        sub = KernTable_format_0()
        sub.version, sub.format, sub.coverage, sub.tupleIndex = 0, 0, 1, 0
        # a format-0 subtable's length field is 16 bits: at most 10,920 pairs
        # (14-byte header + 6 bytes a pair). GPOS carries them all; the legacy
        # table keeps the strongest
        LEGACY_MAX = (0xFFFF - 14) // 6
        sub.kernTable = dict(sorted(kerning.items(), key=lambda kv: -abs(kv[1]))[:LEGACY_MAX])
        kt = newTable("kern"); kt.version = 0; kt.kernTables = [sub]
        fb.font["kern"] = kt
    fb.save(str(path) if isinstance(path, Path) else path)
    return path


def validate_otf(path) -> list[str]:
    """Round-trip through fontTools and run OTS if installed. Returns problems."""
    from fontTools.ttLib import TTFont
    problems = []
    try:
        f = TTFont(str(path))
        cff = "CFF2" if "CFF2" in f else "CFF "              # a variable font carries CFF2
        for tag in (cff, "cmap", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post"):
            if tag not in f:
                problems.append(f"missing table {tag!r}")
        cs = f[cff].cff.topDictIndex[0].CharStrings
        for name in f.getGlyphOrder():
            cs[name].decompile()
    except Exception as e:
        problems.append(f"fontTools round-trip failed: {e}")
    try:
        import ots
    except ImportError:
        return problems
    r = ots.sanitize(str(path), "/dev/null", capture_output=True)
    if r.returncode != 0:
        problems.append("ots-sanitize: " + (r.stderr or r.stdout).decode(errors="replace").strip())
    return problems
