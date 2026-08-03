"""Full (pair-assignment, orientation) Z3 model for Nakseo Yukgodo, ITE-based.

Alternate formulation avoiding bilinear terms:

For each slot t we introduce
    p_t : Int in [1,135]   (all distinct)
    b_t : Bool

Cell values:
    vA(t) = If(b_t, 271 - p_t, p_t)     (B-side the complement)
    vB(t) = 271 - vA(t) = If(b_t, p_t, 271 - p_t)

Structure sums are sums of selected cell-value expressions -> pure linear
arithmetic over {p_t} with ITE guards on constants.
"""
from __future__ import annotations

from z3 import And, Bool, Distinct, If, Int, IntVal, Or, Solver, SolverFor, Sum

from yukgodo.hexgrid import HexGrid, PAIR_SUM


def build_model(grid: HexGrid, timeout_s=300):
    pairs = [Int(f"p{t}") for t in range(135)]
    flips = [Bool(f"b{t}") for t in range(135)]

    cons = []
    for t in range(135):
        cons += [pairs[t] >= 1, pairs[t] <= 135]
    cons.append(Distinct(pairs))

    W = PAIR_SUM  # 271

    def valA(t):
        return If(flips[t], W - pairs[t], pairs[t])

    def valB(t):
        return If(flips[t], pairs[t], W - pairs[t])

    def struct_terms(cells_usage):
        """cells_usage: list over slots of 0 (none), 1 (A), 2 (B) -> sum expr."""
        terms = []
        for t, use in enumerate(cells_usage):
            if use == 1:
                terms.append(valA(t))
            elif use == 2:
                terms.append(valB(t))
        return Sum(terms)

    # Build usage vectors per structure index
    def usage(get_membership):
        out = []
        for t, (a, b) in enumerate(grid.slots):
            ia = get_membership(a)
            ib = get_membership(b)
            out.append((ia, ib))
        return out

    slot_sides = [tuple(grid.sides_of.get(a, ())) for a, _ in grid.slots]
    slot_sides_b = [tuple(grid.sides_of.get(b, ())) for _, b in grid.slots]

    solver = SolverFor("QF_FD")
    solver.set("timeout", timeout_s * 1000)
    solver.add(cons)

    # sides (6)
    for m in range(6):
        terms = []
        for t in range(135):
            if m in slot_sides[t]:
                terms.append(valA(t))
            if m in slot_sides_b[t]:
                terms.append(valB(t))
        solver.add(Sum(terms) == 1355)

    # wedges (6)
    for m in range(6):
        a_i = [t for t in range(135) if grid.wedge_of[grid.slots[t][0]] == m]
        b_i = [t for t in range(135) if grid.wedge_of[grid.slots[t][1]] == m]
        solver.add(Or(
            Sum([valA(t) for t in a_i] + [valB(t) for t in b_i]) == 6097,
            Sum([valA(t) for t in a_i] + [valB(t) for t in b_i]) == 6098,
        ))

    # rays (6); a slot contributes vA to ray m if a on ray m, and vB similarly.
    for m in range(6):
        a_i = [t for t in range(135) if grid.ray_of.get(grid.slots[t][0], -1) == m]
        b_i = [t for t in range(135) if grid.ray_of.get(grid.slots[t][1], -1) == m]
        solver.add(Or(
            Sum([valA(t) for t in a_i] + [valB(t) for t in b_i]) == 1219,
            Sum([valA(t) for t in a_i] + [valB(t) for t in b_i]) == 1220,
        ))

    return flips, pairs, solver
