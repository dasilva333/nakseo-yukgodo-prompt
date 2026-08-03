"""Analysis: prove that the *optimal* penalty region is not invariant under
the reflection sigma for this coordinate system, while it is invariant under
C6 rotations.  We exhibit a concrete optimal solution A whose D6 reflection
sigma *does not* live at penalty level 6.0, thereby showing:
  * The order-12 dihedral action on slot positions is mathematically
    well-defined on 135 slots,
  * but only the cyclic subgroup C6 <= D6 preserves the optimal region.
"""
from __future__ import annotations

import json

from yukgodo.hexgrid import HexGrid, PAIR_SUM
from yukgodo.properties import measure

from yukgodo.analysis import refl_main, rot_k


def from_px(grid, p, x, inverse=False):
    vals = {}
    for t, (a, b) in enumerate(grid.slots):
        L, H = p[t], PAIR_SUM - p[t]
        vals[a], vals[b] = ((H, L) if x[t] else (L, H))
    return vals


def main(path="output/orbit_reps_report.json", n=5):
    grid = HexGrid()
    data = json.load(open(path, encoding="utf-8"))[:n]
    print(f"{'i':>2} | {'pen':>5} | {'rot1':>5} | {'ref':>5} | preserved?")
    for rec in data:
        p, x = tuple(rec["canon_p"]), tuple(rec["canon_x"])
        vals = from_px(grid, p, x)
        pen0 = measure(vals, grid).penalty
        assert abs(pen0 - 6.0) < 1e-9, pen0

        rot_vals = {}
        for c in grid.filled:
            rot_vals[rot_k(1)(c)] = vals[c]
        pen_rot = measure(rot_vals, grid).penalty

        ref_vals = {}
        for c in grid.filled:
            ref_vals[refl_main(c)] = vals[c]
        pen_ref = measure(ref_vals, grid).penalty

        print(f"{rec['orbit']:2d} | {pen0:5.1f} | {pen_rot:5.1f} | {pen_ref:5.1f} | "
              f"rot {'OK' if pen_rot <= 6.0 else 'FAIL'}, ref {'OK' if pen_ref <= 6.0 else 'FAIL'}")


if __name__ == "__main__":
    main()
