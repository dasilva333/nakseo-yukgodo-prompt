"""Enumerate D6-orbit representatives of optimal solutions via Z3.

Model: x_t in {0,1} (flip variable per slot), pair assignment P[t] = t+1 fixed
(WLOG).  Value at slot-cell A = (1-x)*L + x*H, cell B = x*L + (1-x)*H where
L=t+1, H=271-L. So value(A) = L + x*D (D=H-L), value(B) = H - x*D.

Constraints (linear in x):
  sum over side m        = BASE_m + sum coef_t^m x_t = 1355
  sum over wedge m       in {6097, 6098}
  sum over ray m         in {1219, 1220}

Once solver yields word w, canonicalize w -> Can(w) over 12 D6 images and
block the canonical word. Loop until several distinct orbit reps found or UNSAT.
"""
from __future__ import annotations

import sys
import time

from z3 import And, If, Int, IntVal, Or, Solver, Sum, sat

from yukgodo.hexgrid import HexGrid, PAIR_SUM
from yukgodo.analysis import D6, penalties_for_word


def solve(grid: HexGrid, g6: D6, time_limit_s=600, verbose=True, max_reps=4):
    t0 = time.time()
    s = Solver()
    s.set("timeout", time_limit_s * 1000)

    flips = [Int(f"f_{t}") for t in range(135)]
    for f in flips:
        s.add(Or(f == 0, f == 1))

    # Per (structure-index, slot) coefficient: +D if that structure's cell
    # receives the HIGH value when x_t=1, else +low. We encode the total as
    # constant + coef * x_t.
    side_coef = [[0] * 135 for _ in range(6)]
    wedge_coef = [[0] * 135 for _ in range(6)]
    ray_coef = [[0] * 135 for _ in range(6)]
    side_base = [0] * 6
    wedge_base = [0] * 6
    ray_base = [0] * 6

    for t, (a, b) in enumerate(grid.slots):
        L, H = t + 1, PAIR_SUM - (t + 1)
        D = H - L
        # sides
        for m in grid.sides_of.get(a, ()):
            side_base[m] += L
            side_coef[m][t] += D
        for m in grid.sides_of.get(b, ()):
            side_base[m] += H
            side_coef[m][t] -= D
        # wedges (`wedge_of` defined for all non-center cells)
        wa = grid.wedge_of[a]
        wb = grid.wedge_of[b]
        wedge_base[wa] += L
        wedge_base[wb] += H
        wedge_coef[wa][t] += D
        wedge_coef[wb][t] -= D
        # rays
        ra = grid.ray_of.get(a, -1)
        rb = grid.ray_of.get(b, -1)
        if ra >= 0:
            ray_base[ra] += L
            ray_coef[ra][t] += D
        if rb >= 0:
            ray_base[rb] += H
            ray_coef[rb][t] -= D

    def lin(base, coef):
        terms = [IntVal(base)]
        for t in range(135):
            if coef[t] != 0:
                terms.append(IntVal(coef[t]) * flips[t])
        return Sum(terms)

    for m in range(6):
        s.add(lin(side_base[m], side_coef[m]) == 1355)
        s.add(Or(lin(wedge_base[m], wedge_coef[m]) == 6097,
                 lin(wedge_base[m], wedge_coef[m]) == 6098))
        s.add(Or(lin(ray_base[m], ray_coef[m]) == 1219,
                 lin(ray_base[m], ray_coef[m]) == 1220))

    reps = []
    canons = set()
    iters = 0
    while True:
        if time.time() - t0 > time_limit_s:
            if verbose: print(f"[z3] TIMEOUT after {iters} iterations")
            break
        if len(reps) >= max_reps: break
        iters += 1
        rc = s.check()
        if rc != sat:
            if verbose: print(f"[z3] returned {rc} at iter {iters}")
            break
        m = s.model()
        w = tuple(m[f].as_long() for f in flips)
        can = g6.canonical_word(w)
        if can not in canons:
            _, wedge_s, ray_s, pen = penalties_for_word(grid, w)
            assert abs(pen - 6.0) < 1e-9, f"pen={pen} expected 6.0"
            print(f"[z3] NEW ORBIT #{len(reps)} at iter {iters}: pen={pen}, canon[:10]={can[:10]}")
            reps.append(w); canons.add(can)
        # block canonical class
        or_terms = [(flips[t] == (1 - can[t])) for t in range(135)]
        s.add(Or(or_terms))
    return reps, canons


if __name__ == "__main__":
    tl = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    g = HexGrid(); g6 = D6(g)
    reps, canons = solve(g, g6, time_limit_s=tl)
    print(f"\nZ3 found {len(reps)} distinct D6 orbit(s) of optimal solutions.")
