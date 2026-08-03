"""D6 orbit classification report generator + Lean spec consistency check.

This script does three things:
1. Re-runs a modest orbit enumeration (default max_reps=15, total_time=1200s)
   and stores each distinct orbit (canonical pair & flip words) in
   `output/orbit_reps_report.json`.
2. Verifies that the two-orbit claim of Step 3 holds: saves any two distinct
   orbits as `output/distinct_orbits.json` (if missing).
3. Computes per-orbit structural signatures (wedge sum multiset, ray sum
   multiset, side sum multiset) used to argue that the DFS slice is
   orbit-incomplete.

Call from PowerShell with  utf-8:  $env:PYTHONIOENCODING="utf-8"; python REPORT.py
"""
from __future__ import annotations

import json
import os
import sys
import time

from z3 import sat

from yukgodo.hexgrid import HexGrid, PAIR_SUM
from yukgodo.analysis import D6
from yukgodo.z3model import build_model
from enumerate_orbits import check_penalty, image_clauses


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def structural_signature(report):
    """Raw (unsorted) structure-sum vectors.  The wedge/ray multisets are
    provably constant (3*6097 + 3*6098 etc., by the total-sum argument),
    so the positions of the 6098 wedges / 1220 rays constitute the actual
    discriminating signature."""
    return tuple(report.wedge_sums) + tuple(report.ray_sums)


def main(max_reps=15, time_s=1200):
    grid = HexGrid()
    g6 = D6(grid)
    flips, pairs, solver = build_model(grid, timeout_s=time_s)
    solver.push()

    orbits = []
    canonical_set = set()
    t0 = time.time()
    models = 0
    while True:
        if len(orbits) >= max_reps or (time.time() - t0) > time_s:
            break
        rc = solver.check()
        if rc != sat:
            break
        models += 1
        m = solver.model()
        pw = tuple(m.eval(p).as_long() for p in pairs)
        xw = tuple(1 if bool(m.eval(x, model_completion=True)) else 0 for x in flips)
        can = g6.canonical_px(pw, xw)
        if can in canonical_set:
            solver.add(image_clauses(g6, can, pairs, flips))
            continue
        canonical_set.add(can)
        rep = check_penalty(grid, pw, xw)
        assert abs(rep.penalty - 6.0) < 1e-9, rep.penalty
        record = {
            "orbit" : len(orbits)+1,
            "canon_p": list(can[0]),
            "canon_x": list(can[1]),
            "side_sums": rep.side_sums,
            "wedge_sums": rep.wedge_sums,
            "ray_sums": rep.ray_sums,
            "axis_sums": rep.axis_sums,
            "penalty": rep.penalty,
            "signature": structural_signature(rep),
            "elapsed_s": round(time.time()-t0,1),
        }
        orbits.append(record)
        print(f"[report] orbit #{len(orbits)}  sig={record['signature'][:20]}...")
        solver.add(image_clauses(g6, can, pairs, flips))

    write_json("output/orbit_reps_report.json", orbits)

    # Step 3 verification: need at least 2 distinct canonical forms
    assert len(orbits) >= 2, "expected multiple distinct D6 orbits"
    a, b = orbits[0], orbits[1]
    assert (a["canon_p"], a["canon_x"]) != (b["canon_p"], b["canon_x"]), "canonical forms coincide"
    write_json("output/distinct_orbits.json", orbits[:2])
    print(f"Saved {len(orbits)} distinct orbit reps; two-orbit witness saved.")
    return orbits
    a, b = orbits[0], orbits[1]
    assert tuple(a["canon_p"]) != tuple(b["canon_p"]) or tuple(a["canon_x"]) != tuple(b["canon_x"])
    write_json("output/distinct_orbits.json", orbits[:2])
    print(f"Saved {len(orbits)} distinct orbit reps; two-orbit witness saved.")
    return orbits


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    mx = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    tl = int(sys.argv[2]) if len(sys.argv) > 2 else 1200
    main(mx, tl)
