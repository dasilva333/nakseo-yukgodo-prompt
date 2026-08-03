"""Step 4 driver — DFS slice UNSAT.

Proves that the two deterministic pair-assignments along which the
DFS generator from GENERATOR.md/"z3_solver_spec.py" searches are NOT
globally feasible (UNSAT), hence none of the 2^135 orientations of
these slices can be an optimal solution.  Since the DFS image is empty,
it trivially fails orbit completeness.
"""
from __future__ import annotations

import time

from z3 import sat, unknown

from yukgodo.hexgrid import HexGrid, PAIR_SUM
from yukgodo.analysis import D6
from yukgodo.z3model import build_model


def evaluate_slice(grid, g6, p_word, time_s=120):
    """Return (z3 status, wall seconds) for the model with p_t = p_word[t]."""
    flips, pairs, solver = build_model(grid, timeout_s=time_s)
    for t in range(135):
        solver.add(pairs[t] == int(p_word[t]))
    t0 = time.time()
    rc = solver.check()
    return rc, time.time() - t0


def slot_priority(grid):
    """The deterministic DFS slot ordering used in z3_solver_spec.py."""
    def score(s):
        a, b = grid.slots[s]
        side_count = len(grid.sides_of.get(a, ())) + len(grid.sides_of.get(b, ()))
        on_ray = int(grid.ray_of.get(a, -1) >= 0 or grid.ray_of.get(b, -1) >= 0)
        return (side_count, on_ray, s)
    return sorted(range(135), key=score, reverse=True)


def main():
    grid = HexGrid(); g6 = D6(grid)

    # Slice A: naive spiral slot order P[t] = t+1 (default enumeration)
    p_naive = tuple(range(1, 136))
    rc, dt = evaluate_slice(grid, g6, p_naive)
    print(f"[P = naive slot order      ] check={rc} in {dt:.2f}s")

    # Slice B: DFS priority order used by z3_solver_spec.py's pruning DFS
    order = slot_priority(grid)
    p_dfs = tuple(order.index(s) + 1 for s in range(135))
    rc2, dt2 = evaluate_slice(grid, g6, p_dfs)
    print(f"[P = DFS structural order  ] check={rc2} in {dt2:.2f}s")

    # Slice C: reverse DFS priority order, for completeness
    p_rev = tuple(reversed(p_dfs))
    rc3, dt3 = evaluate_slice(grid, g6, p_rev)
    print(f"[P = DFS reverse order     ] check={rc3} in {dt3:.2f}s")

    print()
    print("Interpretation:")
    if rc in ("unsat", None) or str(rc) == "unsat":
        print("  -> Slice A contains NO optimal solution (UNSAT)")
    else:
        print(f"  -> Slice A check returned {rc}")
    if str(rc2) == "unsat":
        print("  -> Slice B contains NO optimal solution (UNSAT)")
    if str(rc3) == "unsat":
        print("  -> Slice C contains NO optimal solution (UNSAT)")
    if all(str(x) == "unsat" for x in (rc, rc2, rc3)):
        print("\nConclusion: deterministic DFS slice (any of these pair orderings) "
              "does not intersect ANY optimal solution.  Its image as a generator is empty.")


if __name__ == "__main__":
    main()
