"""Hand adjustments stored as deltas on semantic names (spec section 5).

Fields (all deltas, all optional):

* ``dx``, ``dy`` -- move a point (skeleton node, outline point, or the
  ``<glyph>.lsb`` / ``<glyph>.rsb`` sidebearings, which use ``dx`` only)
* ``dw`` -- add to the stroke width at a skeleton node (interpolated along
  the adjacent segments)
* ``da`` -- rotate the direction of travel at a skeleton node (degrees)
* ``dt`` -- add to the curve tension at a skeleton node (>0 = flatter)
* ``dp`` -- turn the pen at a skeleton node (degrees; interpolated along the
  adjacent segments, like ``dw``)
* ``dv`` -- per-glyph parameter override: on a name ``<glyph>.@<param>``,
  add ``dv`` to that parameter while compiling that glyph only (written by
  the editor's primitive handles)
* ``stage`` -- ``skeleton`` (default) or ``outline``
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

import yaml

STAGES = ("skeleton", "outline")
DELTAS = ("dx", "dy", "dw", "da", "dt", "dv", "dp")


@dataclass
class Override:
    name: str
    dx: float = 0.0
    dy: float = 0.0
    stage: str = "skeleton"
    dw: float = 0.0
    da: float = 0.0
    dt: float = 0.0
    dv: float = 0.0
    dp: float = 0.0

    def is_zero(self) -> bool:
        return all(abs(getattr(self, k)) < 1e-9 for k in DELTAS)

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in DELTAS if getattr(self, k)}
        if self.stage != "skeleton":
            d["stage"] = self.stage
        return d


def parse_overrides(data: dict | None) -> dict[str, Override]:
    out = {}
    for name, spec in (data or {}).items():
        spec = spec or {}
        stage = spec.get("stage", "skeleton")
        if stage not in STAGES:
            raise ValueError(f"override {name}: unknown stage {stage!r}")
        unknown = set(spec) - set(DELTAS) - {"stage"}
        if unknown:
            raise ValueError(f"override {name}: unknown field(s) {sorted(unknown)}")
        out[name] = Override(name, stage=stage, **{k: float(spec.get(k, 0)) for k in DELTAS})
    return out


def merge_overrides(base: dict[str, Override], extra) -> dict[str, Override]:
    """``base`` with ``extra`` (Overrides, or their dict form as in overrides.yaml)
    added on top: deltas on the same name are summed; a new name takes its own stage."""
    extra = parse_overrides(extra) if extra and not isinstance(next(iter(extra.values())), Override) else (extra or {})
    out = dict(base)
    for name, o in extra.items():
        b = out.get(name)
        out[name] = o if b is None else Override(name, stage=b.stage,
                                                 **{k: getattr(b, k) + getattr(o, k) for k in DELTAS})
    return out


def load_overrides(path) -> dict[str, Override]:
    p = Path(path)
    if not p.exists():
        return {}
    return parse_overrides(yaml.safe_load(p.read_text()))


def _num(v: float) -> str:
    return f"{round(v, 2):g}"


def dump_overrides(ovs: dict[str, Override]) -> str:
    lines = []
    keep = {n: o for n, o in ovs.items() if not o.is_zero()}
    width = max((len(n) for n in keep), default=0) + 1
    for name in sorted(keep):
        o = keep[name]
        parts = [f"{k}: {_num(getattr(o, k))}" for k in DELTAS
                 if k in ("dx", "dy") or getattr(o, k)]
        if o.stage != "skeleton":
            parts.append(f"stage: {o.stage}")
        lines.append(f"{(name + ':').ljust(width)} {{ {', '.join(parts)} }}")
    return "\n".join(lines) + ("\n" if lines else "")


def save_overrides(path, ovs: dict[str, Override]):
    Path(path).write_text(dump_overrides(ovs))


def add_delta(path, name: str, dx: float = 0, dy: float = 0, stage: str = "skeleton",
              **more) -> dict[str, Override]:
    """Accumulate a delta into the overrides file."""
    ovs = load_overrides(path)
    o = ovs.get(name) or Override(name, stage=stage)
    o.dx += dx
    o.dy += dy
    for k, v in more.items():
        setattr(o, k, getattr(o, k) + v)
    ovs[name] = o
    save_overrides(path, ovs)
    return ovs
