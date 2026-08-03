"""Two-orbit witness extraction for Nakseo Yukgodo (洛書六觚圖).

Step 3 of the research prompt: construct explicit optimal solutions
A, B in S* with Can(A) != Can(B) (multiple non-isomorphic D6 orbits).

Approach: run the Z3 enumerator (enumerate_orbits.py); once two distinct
canonical forms have been found, save them (with full cell assignments)
to output/distinct_orbits.json for downstream use and the report.
"""
from __future__ import annotations

import json
import os
import sys
import time

from z3 import Int, Or, sat

from yukgodo.hexgrid import HexGrid, DIRECTIONS
from yukgodo.analysis import D6
from yukgodo.z3model import build_model
from enumerate_orbits import check_penalty


def cell_values(grid, pword, xword):
    w = {}
    for t, (a, b) in enumerate(grid.slots):
        p = pword[t]
        if xword[t] == 0:
            w[a], w[b] = p, 271 - p
        else:
            w[a], w[b] = 271 - p, p
    return w


def cell_word(grid, w):
    """Tuple of values in grid.cells order (the 271-cell arrangement)."""
    return tuple(w.get(c, 0) for c in grid.cells)


def main(out_path="output/distinct_orbits.json", max_reps=2, time_limit_s=3600):
    grid = HexGrid()
    g6 = D6(grid)
    flips, pairs, solver = build_model(grid, timeout_s=time_limit_s)

    seen = set()
    canon_set = set()
    t0 = time.time()
    reps = []
    n_models = 0
    while len(reps) < max_reps and time.time() - t0 < time_limit_s:
        if solver.check() != sat:
            break
        n_models += 1
        m = solver.model()
        pw = tuple(m.eval(p).as_long() for p in pairs)
        xw = tuple(1 if bool(m.eval(x, model_completion=True)) else 0 for x in flips)
        can = g6.canonical_px(pw, xw)
        if can not in canon_set:
            canon_set.add(can)
            rep = check_penalty(grid, pw, xw)
            assert abs(rep.penalty - 6.0) < 1e-9, rep.penalty
            reps.append((pw, xw, can, rep))
            print(f"[z3] orbit #{len(reps)} found (models={n_models}, t={time.time()-t0:.1f}s)")
        # block this canonical form's full D6 orbit
        from enumerate_orbits import image_clauses
        solver.add(image_clauses(g6, can, pairs, flips))

    assert len(reps) >= 2, f"expected >= 2 distinct orbits, got {len(reps)}"
    A_pw, A_xw, A_can, A_rep = reps[0]
    B_pw, B_xw, B_can, B_rep = reps[1]

    out = {
        "A": {
            "p": list(A_pw), "x": list(A_xw),
            "canon_p": list(A_can[0]), "canon_x": list(A_can[1]),
            "cell_values": {f"{q},{r}": v for (q, r), v in cell_values(grid, A_pw, A_xw).items()},
            "cell_word": list(cell_word(grid, cell_values(grid, A_pw, A_xw))),
            "metrics": {
                "side_sums": A_rep.side_sums,
                "wedge_sums": A_rep.wedge_sums,
                "ray_sums": A_rep.ray_sums,
                "axis_sums": A_rep.axis_sums,
                "penalty": A_rep.penalty,
            },
        },
        "B": {
            "p": list(B_pw), "x": list(B_xw),
            "canon_p": list(B_can[0]), "canon_x": list(B_can[1]),
            "cell_values": {f"{q},{r}": v for (q, r), v in cell_values(grid, B_pw, B_xw).items()},
            "cell_word": list(cell_word(grid, cell_values(grid, B_pw, B_xw))),
            "metrics": {
                "side_sums": B_rep.side_sums,
                "wedge_sums": B_rep.wedge_sums,
                "ray_sums": B_rep.ray_sums,
                "axis_sums": B_rep.axis_sums,
                "penalty": B_rep.penalty,
            },
        },
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    can_diff = A_can != B_can
    print(f"\nDistinct orbits: {can_diff}, canonical p[0..5]={A_can[0][:6]} vs {B_can[0][:6]}")
    print(f"Saved to {out_path}")
    return reps


if __name__ == "__main__":
    t_lim = int(sys.argv[1]) if len(sys.argv) > 1 else 3600
    main(time_limit_s=t_lim)
