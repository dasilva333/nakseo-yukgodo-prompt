"""Simplest correct two-orbit witness using the already-validated solve_one.py
machinery and a robust canonicalization on the ACTUAL slot-word representation.
"""
from __future__ import annotations

import json
import time

from z3 import Bool, Not, Or, Int, IntVal, Solver as RawSolver, sat, Distinct, Sum

from yukgodo.hexgrid import HexGrid
from yukgodo.analysis import D6, penalties_for_px

PAIR_SUM = 271


def solve_px(grid, timeout_s=120, blocking_orbits=None):
    """Solve one optimal model in (p, x) coordinates directly via Int/Distinct.
    Returns (p_word, x_word) or None."""
    N = 135
    pairs = [Int(f"p_{t}") for t in range(N)]
    flips = [Bool(f"b_{t}") for t in range(N)]
    solver = RawSolver()
    solver.set("timeout", timeout_s * 1000)
    for t in range(N):
        solver.add(1 <= pairs[t], pairs[t] <= N)
    solver.add(Distinct(pairs))

    W = PAIR_SUM
    from z3 import If

    def vA(t):
        return If(flips[t], W - pairs[t], pairs[t])

    def vB(t):
        return If(flips[t], pairs[t], W - pairs[t])

    # Side sums (each side has 10 cells = 10 contributing slots)
    for m in range(6):
        terms = []
        for t, (a, b) in enumerate(grid.slots):
            if m in grid.sides_of.get(a, ()):
                terms.append(vA(t))
            if m in grid.sides_of.get(b, ()):
                terms.append(vB(t))
        assert len(terms) == 10, len(terms)
        solver.add(Sum(terms) == 1355)
    # Wedges
    for m in range(6):
        terms = []
        for t, (a, b) in enumerate(grid.slots):
            if grid.wedge_of[a] == m: terms.append(vA(t))
            if grid.wedge_of[b] == m: terms.append(vB(t))
        assert len(terms) == 45, len(terms)
        expr = Sum(terms)
        solver.add(Or(expr == 6097, expr == 6098))
    # Rays
    for m in range(6):
        terms = []
        for t, (a, b) in enumerate(grid.slots):
            if grid.ray_of.get(a, -1) == m: terms.append(vA(t))
            if grid.ray_of.get(b, -1) == m: terms.append(vB(t))
        assert len(terms) == 9, len(terms)
        expr = Sum(terms)
        solver.add(Or(expr == 1219, expr == 1220))

    # Block given orbits (canonical words)
    if blocking_orbits:
        for (pw, xw) in blocking_orbits:
            solver.add(Or(
                *[pairs[t] != IntVal(int(pw[t])) for t in range(N)],
                *[(Not(flips[t]) if xw[t] else flips[t]) for t in range(N)],
            ))

    rc = solver.check()
    if rc != sat:
        return None
    m = solver.model()
    pw = tuple(m.eval(p).as_long() for p in pairs)
    xw = tuple(1 if bool(m.eval(x, model_completion=True)) else 0 for x in flips)
    # verify
    _, _, _, pen = penalties_for_px(grid, pw, xw)
    assert abs(pen - 6.0) < 1e-9, f"pen={pen}"
    return pw, xw


def main(n_orbits=6, time_s=900):
    grid = HexGrid(); g6 = D6(grid)
    seen = []
    t0 = time.time()
    out = []
    while len(out) < n_orbits and time.time() - t0 < time_s:
        blocking = [ (c[0], c[1]) for c in seen ]
        res = solve_px(grid, timeout_s=120, blocking_orbits=blocking)
        if res is None:
            print("UNSAT: orbit space exhausted", flush=True)
            break
        pw, xw = res
        can = g6.canonical_px(pw, xw)
        if can in seen:
            print("repeat!", flush=True)
            continue
        seen.append(can)
        _, wedge, ray, pen = penalties_for_px(grid, *can)
        print(f"orbit #{len(out)}: pen={pen:.1f} canon_p[:6]={can[0][:6]} wedges={wedge} rays={ray}", flush=True)
        out.append(can)

    with open("output/final_orbits.json", "w", encoding="utf-8") as f:
        json.dump([
            {"canon_p": list(c[0]), "canon_x": list(c[1])} for c in out
        ], f, ensure_ascii=False, indent=2)

    print(f"\nCaptured {len(out)} distinct optimal D6 orbits (verified pen=6.0)!")
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    tl = int(sys.argv[2]) if len(sys.argv) > 2 else 900
    main(n, tl)
