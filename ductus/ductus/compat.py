"""Make master outlines point-compatible without changing their shapes.

Overlap removal re-segments curves as strokes get heavier or lighter (new
intersections, near-degenerate bits dropped), so a glyph's merged outline at
two weights can draw the same kind of shape with different point structures.
A variable font needs identical structures. This module unifies them exactly:

1. contours are matched between masters (by position and winding);
2. corners (on-curve points where the outline turns sharply) are found on
   each contour and aligned, starting from the corner nearest the
   reference's first;
3. between consecutive corners every segment becomes a cubic (a line
   exactly) and segments are split by de Casteljau (exact) at a shared set
   of arc-length positions, until every master has the same segments.

The shapes are unchanged; only the point structure is unified. It fails
(returns None) when masters differ in contour count or corner count -- a
real change of topology, which the caller reports.
"""
from __future__ import annotations

import math

import numpy as np

from .geometry import Contour

SAMPLES = 24


def segments(c: Contour) -> list[np.ndarray]:
    """The contour as closed cubic segments (4x2 arrays); lines are elevated."""
    pts, types = c.pts, c.types
    n = len(pts)
    segs, i = [], 0
    while i < n:
        p0 = np.array(pts[i], float)
        j = (i + 1) % n
        if types[j] == "off":
            c1, c2 = np.array(pts[j], float), np.array(pts[(i + 2) % n], float)
            p3 = np.array(pts[(i + 3) % n], float)
            segs.append(np.array([p0, c1, c2, p3]))
            i += 3
        else:
            p3 = np.array(pts[j], float)
            segs.append(np.array([p0, p0 + (p3 - p0) / 3, p0 + 2 * (p3 - p0) / 3, p3]))
            i += 1
    return segs


def from_segments(segs: list[np.ndarray]) -> Contour:
    c = Contour()
    c.add(segs[0][0])
    for k, s in enumerate(segs):
        c.add(s[1], "off")
        c.add(s[2], "off")
        if k < len(segs) - 1:
            c.add(s[3])
    return c


def _point(s, t):
    mt = 1 - t
    return mt ** 3 * s[0] + 3 * mt * mt * t * s[1] + 3 * mt * t * t * s[2] + t ** 3 * s[3]


def _split(s, t):
    """De Casteljau: the segment split at t into two (exact)."""
    a = s[0] + (s[1] - s[0]) * t
    b = s[1] + (s[2] - s[1]) * t
    c = s[2] + (s[3] - s[2]) * t
    d = a + (b - a) * t
    e = b + (c - b) * t
    f = d + (e - d) * t
    return np.array([s[0], a, d, f]), np.array([f, e, c, s[3]])


def _length_table(s):
    ts = np.linspace(0, 1, SAMPLES + 1)
    p = np.array([_point(s, t) for t in ts])
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    return ts, d


def _length(s):
    return _length_table(s)[1][-1]


def _t_at(s, frac):
    """The parameter at ``frac`` of the segment's arc length."""
    ts, d = _length_table(s)
    if d[-1] <= 1e-9:
        return frac
    return float(np.interp(frac * d[-1], d, ts))


def _tangent_out(s):
    for k in (2, 1, 0):
        v = s[3] - s[k]
        if np.linalg.norm(v) > 1e-6:
            return v
    return np.array([1.0, 0.0])


def _tangent_in(s):
    for k in (1, 2, 3):
        v = s[k] - s[0]
        if np.linalg.norm(v) > 1e-6:
            return v
    return np.array([1.0, 0.0])


def corners(segs, thr_deg: float) -> list[int]:
    """Indices j where segment j starts at a corner (the outline turns more
    than ``thr_deg`` there)."""
    out = []
    n = len(segs)
    for j in range(n):
        a, b = _tangent_out(segs[j - 1]), _tangent_in(segs[j])
        cos = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        if math.degrees(math.acos(max(-1.0, min(1.0, cos)))) > thr_deg:
            out.append(j)
    return out


def _corner_feats(segs, idx, box):
    """Per corner: position relative to the ink box's centre, and the unit
    tangents in and out (stable across weights, unlike positions)."""
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    out = []
    for j in idx:
        a, b = _tangent_out(segs[j - 1]), _tangent_in(segs[j])
        out.append((np.array([segs[j][0][0] - cx, segs[j][0][1] - cy]),
                    a / np.linalg.norm(a), b / np.linalg.norm(b)))
    return out


def _align(rf, mf, max_cost=3.0):
    """Monotone cyclic alignment of the reference's corners ``rf`` to a
    master's ``mf``: [(i, j)] matched pairs, minimising match costs plus a
    penalty of 1 per unmatched corner, over every cyclic offset."""
    a, b = len(rf), len(mf)
    if not a or not b:
        return []

    def cost(i, j):
        (p, ti, to), (q, ui, uo) = rf[i], mf[j]
        ang = (1 - float(np.dot(ti, ui))) + (1 - float(np.dot(to, uo)))     # 0 .. 4
        return float(np.linalg.norm(p - q)) / 60.0 + ang * 2.0
    C = [[cost(i, j) for j in range(b)] for i in range(a)]
    best = None
    for s in range(b):
        # dp over reference i and master (j rotated by s)
        INF = 1e9
        dp = [[INF] * (b + 1) for _ in range(a + 1)]
        bk = [[None] * (b + 1) for _ in range(a + 1)]
        dp[0][0] = 0.0
        for i in range(a + 1):
            for j in range(b + 1):
                v = dp[i][j]
                if v >= INF:
                    continue
                if i < a and v + 1.0 < dp[i + 1][j]:
                    dp[i + 1][j], bk[i + 1][j] = v + 1.0, (i, j, None)
                if j < b and v + 1.0 < dp[i][j + 1]:
                    dp[i][j + 1], bk[i][j + 1] = v + 1.0, (i, j, None)
                if i < a and j < b:
                    c = C[i][(j + s) % b]
                    if c < max_cost and v + c < dp[i + 1][j + 1]:
                        dp[i + 1][j + 1], bk[i + 1][j + 1] = v + c, (i, j, (i, (j + s) % b))
        if best is None or dp[a][b] < best[0]:
            pairs, i, j = [], a, b
            while (i, j) != (0, 0):
                pi, pj, m = bk[i][j]
                if m:
                    pairs.append(m)
                i, j = pi, pj
            best = (dp[a][b], pairs[::-1])
    return best[1]


def _norm(p, box):
    x0, y0, x1, y1 = box
    return np.array([(p[0] - x0) / max(x1 - x0, 1.0), (p[1] - y0) / max(y1 - y0, 1.0)])


def _box(contours):
    xs = [p[0] for c in contours for p in c.pts]
    ys = [p[1] for c in contours for p in c.pts]
    return (min(xs), min(ys), max(xs), max(ys))


def _rotate(segs, j):
    return segs[j:] + segs[:j]


def _unify_spans(spans_by_master, tol=0.01):
    """``spans_by_master[m]`` = one span's segments in master m. Split them so
    every master has segment boundaries at corresponding arc-length
    fractions: all masters' boundaries are clustered (single linkage within
    ``tol``); in each cluster every master gets as many boundaries as the
    master with the most (its own, then splits at the cluster's mean -- a
    repeated split leaves a degenerate segment, harmless to interpolate)."""
    per_master = []
    for segs in spans_by_master:
        L = [_length(s) for s in segs]
        tot = sum(L) or 1.0
        per_master.append((segs, L, tot, list(np.cumsum(L)[:-1] / tot)))
    allb = sorted((b, m) for m, (_, _, _, bs) in enumerate(per_master) for b in bs)
    clusters = []
    for b, m in allb:
        if clusters and b - clusters[-1][-1][0] <= tol:
            clusters[-1].append((b, m))
        else:
            clusters.append([(b, m)])
    out = []
    for m, (segs, L, tot, bs) in enumerate(per_master):
        need = []
        for c in clusters:
            want = max(sum(1 for _, mm in c if mm == k) for k in range(len(per_master)))
            have = sum(1 for _, mm in c if mm == m)
            need += [float(np.mean([b for b, _ in c]))] * (want - have)
        need.sort()
        new, acc = [], 0.0
        for k, (s, l) in enumerate(zip(segs, L)):
            start, end = acc / tot, (acc + l) / tot
            last = k == len(segs) - 1
            cut = [f for f in need if start <= f < end or (last and f >= start)]
            need = [f for f in need if f not in cut] if cut else need
            rest, done = s, start
            for f in cut:
                a, rest = _split(rest, _t_at(rest, min(max((f - done) / max(end - done, 1e-12), 0.0), 1.0)))
                new.append(a)
                done = max(done, f)
            new.append(rest)
            acc += l
        out.append(new)
    if len({len(o) for o in out}) != 1:
        return None
    return out


def _match_contours(ref, other):
    """Permutation of ``other`` matching ``ref`` by bbox-normalised centroid
    and winding, or None."""
    if len(ref) != len(other):
        return None
    rb, ob = _box(ref), _box(other)

    def key(c, box):
        p = np.mean(np.array(c.pts), axis=0)
        return _norm(p, box), (c.area() > 0)
    rk = [key(c, rb) for c in ref]
    ok = [key(c, ob) for c in other]
    used, perm = set(), []
    for rp, rw in rk:
        best = None
        for j, (op, ow) in enumerate(ok):
            if j in used or ow != rw:
                continue
            d = float(np.linalg.norm(rp - op))
            if best is None or d < best[0]:
                best = (d, j)
        if best is None:
            return None
        used.add(best[1])
        perm.append(best[1])
    return perm


LAST_FAIL = ""


def _fail(why: str):
    """Record why the last ``compatible`` call failed (for reports) and fail."""
    global LAST_FAIL
    LAST_FAIL = why
    return None


def compatible(masters: list[list[Contour]], thresholds=(20.0, 12.0, 30.0, 45.0)) -> list[list[Contour]] | None:
    """Point-compatible copies of each master's contours (masters[0] is the
    reference whose contour order and start points the others follow), or
    None when they can't be made compatible without changing shape."""
    ref = masters[0]
    if not ref:
        return [[] for _ in masters] if all(not m for m in masters) else None
    perms = [_match_contours(ref, m) for m in masters]
    if any(p is None for p in perms):
        return _fail(f"contours: {[len(m) for m in masters]}")
    boxes = [_box(m) for m in masters]
    out = [[] for _ in masters]
    for i in range(len(ref)):
        cs = [masters[k][perms[k][i]] for k in range(len(masters))]
        segs = [segments(c) for c in cs]
        # the reference's corners anchor the spans: each master's corners are
        # aligned to them (position and tangents), and only the reference
        # corners matched in every master are kept
        cn_all = [corners(sg, thresholds[0]) for sg in segs]
        rf = _corner_feats(segs[0], cn_all[0], boxes[0])
        matched = [dict(_align(rf, _corner_feats(segs[k], cn_all[k], boxes[k]))) for k in range(1, len(masters))]
        keep = [i0 for i0 in range(len(cn_all[0])) if all(i0 in m for m in matched)]
        if keep:
            maps = [[cn_all[0][i0] for i0 in keep]] + \
                   [[cn_all[k + 1][matched[k][i0]] for i0 in keep] for k in range(len(masters) - 1)]
            for k, mk in enumerate(maps):
                rel = [(x - mk[0]) % len(segs[k]) for x in mk]
                if rel != sorted(rel) or len(set(mk)) != len(mk):
                    return _fail(f"contour {i}: corner order differs")
        else:
            # no shared corners: start each master at the joint nearest the reference's first
            a0 = _norm(segs[0][0][0], boxes[0])
            maps = [[min(range(len(sg)), key=lambda j: float(np.linalg.norm(_norm(sg[j][0], boxes[k]) - a0)))]
                    for k, sg in enumerate(segs)]
        segs = [_rotate(segs[k], maps[k][0]) for k in range(len(masters))]
        cn = [sorted((c - maps[k][0]) % len(segs[k]) for c in maps[k]) for k in range(len(masters))]
        # spans between corners (the whole contour when there are none)
        spans = []
        for k in range(len(masters)):
            cuts = cn[k] if cn[k] else [0]
            cuts = cuts + [len(segs[k])]
            spans.append([segs[k][cuts[q]:cuts[q + 1]] for q in range(len(cuts) - 1)])
        if len({len(s) for s in spans}) != 1:
            return _fail(f"contour {i}: span counts differ")
        unified = [[] for _ in masters]
        for q in range(len(spans[0])):
            u = _unify_spans([spans[k][q] for k in range(len(masters))])
            if u is None:
                return _fail(f"contour {i}: span {q} won't unify")
            for k in range(len(masters)):
                unified[k] += u[k]
        for k in range(len(masters)):
            out[k].append(from_segments(unified[k]))
    return out
