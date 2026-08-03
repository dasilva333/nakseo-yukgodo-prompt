"""Preamble solver: find ONE optimal Nakseo Yukgodo solution via Z3."""
from __future__ import annotations

import sys
import time

from z3 import sat

from yukgodo.hexgrid import HexGrid
from yukgodo.analysis import D6
from yukgodo.z3model import build_model
from enumerate_orbits import check_penalty


def main(time_s=300):
    grid = HexGrid()
    g6 = D6(grid)
    flips, pairs, solver = build_model(grid)

    print("solver built, running check...", flush=True)
    t0 = time.time()
    rc = solver.check()
    print(f"solver returned {rc} in {time.time()-t0:.2f}s", flush=True)
    if rc != sat:
        sys.exit(1)
    m = solver.model()
    pw = tuple(m.eval(p, model_completion=True).as_long() for p in pairs)
    xw = tuple(bool(m.eval(x, model_completion=True)) for x in flips)
    xw = tuple(1 if v else 0 for v in xw)
    rep = check_penalty(grid, pw, xw)
    print(f"penalty = {rep.penalty}")
    print(f"side_sums = {rep.side_sums}")
    print(f"wedge_sums = {rep.wedge_sums}")
    print(f"ray_sums = {rep.ray_sums}")
    can = g6.canonical_px(pw, xw)
    print(f"canonical p[:8]={can[0][:8]}")
    print(f"canonical x[:8]={can[1][:8]}")


if __name__ == "__main__":
    tl = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    main(tl)
