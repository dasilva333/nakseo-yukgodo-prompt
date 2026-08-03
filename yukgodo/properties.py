"""Measurement and scoring of the magic properties of a placement.

For a placement (values: cell → a number from 1..270), measures the
properties that can be checked against the commentary.

Derivation of the targets (antipodal complementary-pair hypothesis: the
two cells of a point-symmetric pair sum to 271):

    - ring k sum    = 3k × 271 = 813k       (ring k holds 3k antipodal pairs)
    - side sum      = 5 × 271 = 1355        (opposite sides balance to 2710
                                             automatically)
    - sector (觚) sum ≈ 12195 / 2 = 6097.5  (45 cells is odd, so exact equality
                                             is impossible; the optimum
                                             alternates 6097/6098)
    - ray sum       ≈ 2439 / 2 = 1219.5     (a pair of opposite rays = 9 × 271)
    - axis (中觚) sum = 9 × 271 = 2439      (automatic under the pair hypothesis)

penalty is the total absolute deviation from the targets, and its
theoretical floor is 6.0 (sector 3.0 + ray 3.0; the odd cell counts make
0 unreachable).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .hexgrid import (
    N_FILLED,
    OUTER_RING,
    PAIR_SUM,
    TOTAL_SUM,
    HexGrid,
    antipode,
    ring_of,
)

SIDE_TARGET = 5 * PAIR_SUM               # 1355
WEDGE_TARGET = 45 * PAIR_SUM / 2         # 6097.5
RAY_TARGET = 9 * PAIR_SUM / 2            # 1219.5
AXIS_TARGET = 9 * PAIR_SUM               # 2439
PENALTY_FLOOR = 6.0                      # half-cell error limit of sectors and rays


def ring_target(k: int) -> int:
    """Target sum of ring k = 813k (通加洛書數六倍: the total 6×45×271/2 distributed per ring)."""
    return 3 * k * PAIR_SUM


@dataclass
class PropertyReport:
    """Property measurements for one placement."""

    ring_sums: list[int]                 # rings 0..9 (0 is the center = 0)
    side_sums: list[int]                 # 6 sides
    wedge_sums: list[int]                # 6 sectors
    ray_sums: list[int]                  # 6 rays
    axis_sums: list[int]                 # 3 axes (including 中觚)
    pair_devs: list[int]                 # antipodal pair sum − 271, per slot
    corner_values: list[int]             # 6 perimeter corner values
    total: int                           # grand total (for validation: 36585)
    penalty: float = 0.0
    parts: dict[str, float] = field(default_factory=dict)


def measure(values: dict, grid: HexGrid) -> PropertyReport:
    """Measure every property of a placement."""
    ring_sums = [0] * (grid.radius + 1)
    for c, v in values.items():
        ring_sums[ring_of(c)] += v

    side_sums = [sum(values[c] for c in side) for side in grid.sides]
    wedge_sums = [sum(values[c] for c in wedge) for wedge in grid.wedges]
    ray_sums = [sum(values[c] for c in ray) for ray in grid.rays]
    axis_sums = [
        sum(values.get(c, 0) for c in axis) for axis in grid.axes
    ]
    pair_devs = [
        values[a] + values[b] - PAIR_SUM for a, b in grid.slots
    ]
    corner_values = [values[c] for c in grid.corners()]
    total = sum(values.values())

    parts = {
        "sides": sum(abs(s - SIDE_TARGET) for s in side_sums),
        "wedges": sum(abs(w - WEDGE_TARGET) for w in wedge_sums),
        "rays": sum(abs(r - RAY_TARGET) for r in ray_sums),
        "pairs": sum(abs(d) for d in pair_devs),
        "rings": sum(
            abs(ring_sums[k] - ring_target(k)) for k in range(1, grid.radius + 1)
        ),
        "axes": sum(abs(s - AXIS_TARGET) for s in axis_sums),
    }
    penalty = sum(parts.values())
    return PropertyReport(
        ring_sums=ring_sums,
        side_sums=side_sums,
        wedge_sums=wedge_sums,
        ray_sums=ray_sums,
        axis_sums=axis_sums,
        pair_devs=pair_devs,
        corner_values=corner_values,
        total=total,
        penalty=penalty,
        parts=parts,
    )


def validate(values: dict, grid: HexGrid) -> list[str]:
    """Check a placement against the basic conditions and return the list of violations."""
    errors: list[str] = []
    if len(values) != N_FILLED:
        errors.append(f"filled cell count {len(values)} != {N_FILLED}")
    extra = [c for c in values if c not in grid.cell_set or c == (0, 0)]
    if extra:
        errors.append(f"{len(extra)} cells lie outside the lattice or at the center")
    vals = sorted(values.values())
    if vals != list(range(1, N_FILLED + 1)):
        errors.append("values do not use each of 1..270 exactly once")
    if sum(vals) != TOTAL_SUM:
        errors.append(f"total sum {sum(vals)} != {TOTAL_SUM}")
    outer = [c for c in values if ring_of(c) == OUTER_RING]
    if len(outer) != 54:
        errors.append(f"perimeter cell count {len(outer)} != 54")
    return errors
