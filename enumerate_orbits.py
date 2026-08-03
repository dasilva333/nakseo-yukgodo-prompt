"""Orbit enumerator with clean canonical-class blocking.

Enumerates distinct D6 orbit representatives among all optimal solutions.
When a model is found, its orbit canonical form is computed and ALL 12 D6
images of that canonical form are blocked via a single clause `Not(And(...))`
per image. This keeps each clause small.

Because the number of orbits may be huge, a time cap and representative
cap default to safe values and can be increased via CLI.

Outputs JSONL: one record per canonical representative.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from z3 import And, IntVal, Not, BoolVal, Or, sat

from yukgodo.hexgrid import HexGrid, PAIR_SUM
from yukgodo.analysis import D6
from yukgodo.z3model import build_model


def check_penalty(grid, pword, xword):
    """Independent verification through the cell-value dictionary."""
    from yukgodo.properties import measure
    vals = {}
    for t, (a, b) in enumerate(grid.slots):
        L, H = pword[t], PAIR_SUM - pword[t]
        va, vb = (H, L) if xword[t] else (L, H)
        vals[a] = va
        vals[b] = vb
    return measure(vals, grid)


def image_clauses(g6: D6, can, pairs, flips):
    """For each of the 12 D6 images of `can`, return a clause `model != image`."""
    from z3 import Not as _N
    orbit = g6.orbit_words(can[0], can[1])
    out = []
    for (op, ox) in orbit:
        out.append(Or(
            *[pairs[t] != IntVal(int(op[t])) for t in range(135)],
            *[(_N(flips[t]) if ox[t] else flips[t]) for t in range(135)],
        ))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-reps", type=int, default=40)
    ap.add_argument("--time", type=int, default=2400, help="total wall-clock seconds")
    ap.add_argument("--out", default="output/all_orbits.jsonl")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    grid = HexGrid()
    g6 = D6(grid)
    flips, pairs, solver = build_model(grid, timeout_s=args.time)

    canon_set = set()
    t0 = time.time()
    n_models = 0
    n_reps = 0
    while time.time() - t0 < args.time and n_reps < args.max_reps:
        if solver.check() != sat:
            print("[enum] UNSAT: orbit space exhausted", flush=True)
            break
        n_models += 1
        m = solver.model()
        pw = tuple(m.eval(p, model_completion=True).as_long() for p in pairs)
        xw = tuple(1 if bool(m.eval(x, model_completion=True)) else 0 for x in flips)
        can = g6.canonical_px(pw, xw)
        if can not in canon_set:
            rep = check_penalty(grid, pw, xw)
            assert abs(rep.penalty - 6.0) < 1e-9, rep.penalty
            canon_set.add(can)
            n_reps += 1
            rec = {
                "orbit_index": n_reps,
                "canon_p": list(can[0]),
                "canon_x": list(can[1]),
                "metrics": {
                    "side_sums": rep.side_sums,
                    "wedge_sums": rep.wedge_sums,
                    "ray_sums": rep.ray_sums,
                    "penalty": rep.penalty,
                },
                "model_index": n_models,
                "elapsed_s": round(time.time() - t0, 2),
            }
            with open(args.out, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[enum] orbit #{n_reps} (models={n_models}, t={time.time()-t0:.1f}s, "
                  f"w={rep.wedge_sums}, r={rep.ray_sums})", flush=True)
        # block this canonical form's full D6 orbit
        solver.add(image_clauses(g6, can, pairs, flips))

    print(f"\nTOTAL: {n_reps} distinct D6 orbits enumerated in {time.time()-t0:.1f}s "
          f"({n_models} models checked)")


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
    main()
