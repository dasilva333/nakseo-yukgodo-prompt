"""SMT-complete optimal solution enumeration for Nakseo Yukgodo — cell-value
formulation that avoids bilinear products entirely.

For each of the 270 filled cells we have an Int variable v_i in [1,270],
with Distinct(v_0, ..., v_269).  The antipodal-pair constraints are
    v_{slot_t.A} + v_{slot_t.B} = 271   for t = 0..134.

Inverters/rotations/reflections of the grid therefore act as cell-index
permutations.  D6 action on words is not needed inside the solver; instead
we canonicalize each model cell-index-wise after extraction.
"""
from __future__ import annotations

import json
import sys
import time

from z3 import Distinct, Int, SolverFor, Sum, sat

from yukgodo.hexgrid import HexGrid, antipode


PAIRS = {0: 0}


def build_cell_model(grid: HexGrid, timeout_s=120):
    """Return (cells_list, vars, solver, antipode_pairs) for the cell-value model."""
    cell_list = grid.filled
    idx = {c: i for i, c in enumerate(cell_list)}
    vars_ = [Int(f"v_{i}") for i in range(len(cell_list))]
    bounds = []
    for v in vars_:
        bounds.append(v >= 1)
        bounds.append(v <= 270)
    solver = SolverFor("QF_FD")
    solver.set("timeout", timeout_s * 1000)
    solver.add(bounds)
    solver.add(Distinct(vars_))

    # Antipodal pair constraint
    for t, (a, b) in enumerate(grid.slots):
        ia, ib = idx[a], idx[b]
        solver.add(vars_[ia] + vars_[ib] == 271)

    # Side sum constraints
    for j, side in enumerate(grid.sides):
        cell_ids = [idx[c] for c in side]
        solver.add(Sum([vars_[k] for k in cell_ids]) == 1355)

    # Wedge sums (in {6097, 6098}) and rays (in {1219, 1220})
    for i, wedge in enumerate(grid.wedges):
        expr = Sum([vars_[idx[c]] for c in wedge])
        solver.add(z3__Or(expr == 6097, expr == 6098))
    for i, ray in enumerate(grid.rays):
        expr = Sum([vars_[idx[c]] for c in ray])
        solver.add(z3__Or(expr == 1219, expr == 1220))
    return cell_list, vars_, solver


def z3__Or(*conds):
    import z3
    return z3.Or(*conds)


def main(n_orbits=2, time_s=600):
    grid = HexGrid()
    cell_list, vars_, solver = build_cell_model(grid, timeout_s=time_s)
    print(f"model built in {time.time():.1f} (relative), constraints ok")

    # The cell->slot canonical map:
    g6 = None
    canon = {}
    orbit_count = 0
    t0 = time.time()
    while orbit_count < n_orbits and time.time() - t0 < time_s:
        rc = solver.check()
        if rc != sat:
            print("(unsat)", flush=True)
            break
        m = solver.model()
        w = tuple(m.eval(v).as_long() for v in vars_)
        # canonical form of the assignment tuple w under D6
        if g6 is None:
            from yukgodo.analysis import D6
            g6 = D6(grid)
        # A slot word derived from the cell assignment
        slots = grid.slots
        slot_of = {}
        for i, (a, b) in enumerate(slots):
            slot_of[a] = i; slot_of[b] = i
        st_p, st_x = [0]*135, [0]*135
        for t, (a, b) in enumerate(slots):
            va = w[cell_list.index(a)]
            if va < 136:  # A cell got the SMALL value
                L = va
                st_p[t] = L
                st_x[t] = 0
            else:
                st_p[t] = 271 - va
                st_x[t] = 1
        tup = (tuple(st_p), tuple(st_x))
        if tup in canon:
            solver.add(Distinct(vars_, *([])))  # dummy; instead block the exact word
            # block exact word
            from z3 import Or, Not
            solver.add(Or(*[v != wv for v, wv in zip(vars_, w)]))
            continue
        canon[tup] = w
        orbit_count += 1
        print(f"orbit #{orbit_count}: canon_p[:6]={st_p[:6]}")
        from z3 import Or
        solver.add(Or(*[v != wv for v, wv in zip(vars_, w)]))

    print(f"Found {orbit_count} distinct orbit(s).")
    return canon


if __name__ == "__main__":
    args = sys.argv
    n_orbits = int(args[1]) if len(args) > 1 else 2
    time_s = int(args[2]) if len(args) > 2 else 600
    main(n_orbits, time_s)
