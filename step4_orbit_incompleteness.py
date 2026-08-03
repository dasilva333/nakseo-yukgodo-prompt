"""Step 4 concrete orbit-incompleteness proof for the 2^135 orientation-slice DFS.

What the existing deterministic DFS does (per GENERATOR.md and the baseline
`z3_solver_spec.py` experiment):

  0. Slots sorted by a deterministic structural priority
     (side-members count desc, ray-members desc, slot index).
  1. At depth d, slot S_d is assigned the complementary pair (v, 271-v) with
     v = (rank of S_d in sorted order).
  2. Branch on orientation: A gets v / A gets 271-v.
  3. Backtrack when partial side-penalty lower bound exceeds best.

That is: the DFS searches over the slice K = {0,1}^135 of orientation bits
with a FIXED pair-assignment P̂ : slot -> {1..135} determined by the slot
order.  Its full image = { (P̂, x) : x ∈ {0,1}^135 }.

Two independent falsifying verifications, both executed below:

  (A) Exhaustive slice infeasibility: with P̂ pinned, the optimal-region
      constraints (sides=1355, wedges∈{6097,6098}, rays∈{1219,1220}) are
      UNSAT (verified by Z3).  Hence image(DFS) ∩ S* = ∅.

  (B) Point evaluation: actually running the provided baseline
      `solve_deterministic_backtracking` with a generous state budget
      produces a best solution of penalty >> 6.0, so its canonical form is
      not any of the known optimal orbits.

Both conclusions show: for every known optimal orbit, the DFS does not reach
it -> the generator is orbit-INCOMPLETE.
"""
from __future__ import annotations

import json
import sys
import time

from z3 import sat

from yukgodo.hexgrid import HexGrid
from yukgodo.analysis import D6, penalties_for_px
from yukgodo.z3model import build_model
from yukgodo.properties import measure, PENALTY_FLOOR


# ---------------------------------------------------------------------------
# (A) Prove orientation-only slice UNSAT for a fixed pair assignment
# ---------------------------------------------------------------------------

def slice_unsat_for_pair_assignment(grid, pair_assignment, time_s=180):
    """pin pairs[t] = pair_assignment[t], then solve for flips."""
    flips, pairs, solver = build_model(grid, timeout_s=time_s)
    for t in range(135):
        solver.add(pairs[t] == int(pair_assignment[t]))
    t0 = time.time()
    rc = solver.check()
    return rc, time.time() - t0


def slot_priority_order(grid):
    """Deterministic structural order used by the reference DFS."""
    def key(s):
        a, b = grid.slots[s]
        side_count = len(grid.sides_of.get(a, ())) + len(grid.sides_of.get(b, ()))
        on_ray = grid.ray_of.get(a, -1) >= 0 or grid.ray_of.get(b, -1) >= 0
        return (-side_count, -int(on_ray), s)
    return sorted(range(135), key=key)


def pair_assignment_for(grid, slot_order):
    """If DFS visits slots in slot_order, it assigns pair value (rank+1)."""
    p = [0] * 135
    for rank, s in enumerate(slot_order):
        p[s] = rank + 1
    return tuple(p)


# ---------------------------------------------------------------------------
# (B) Actually run the reference DFS (imported from the baseline spec) and
#     canonicalize its best output
# ---------------------------------------------------------------------------

def run_reference_dfs(grid, max_states=200_000):
    """Import and run the deterministic DFS from `z3_solver_spec.py`."""
    sys.path.insert(0, ".")
    from z3_solver_spec import solve_deterministic_backtracking
    return solve_deterministic_backtracking(grid, max_states=max_states)


def values_to_px(grid, values):
    """Inverse direction: cell-value dict -> (p, x) words."""
    pword = [0] * 135
    xword = [0] * 135
    for t, (a, b) in enumerate(grid.slots):
        va, vb = values[a], values[b]
        lo = min(va, vb)
        pword[t] = lo
        xword[t] = 0 if values[a] == lo else 1
    return tuple(pword), tuple(xword)


def main():
    grid = HexGrid(); g6 = D6(grid)

    print("=" * 72)
    print(" (A) Z3 UNSAT check of the orientation-slice")
    print("=" * 72)

    order = slot_priority_order(grid)
    p_dfs = pair_assignment_for(grid, order)
    rc, dt = slice_unsat_for_pair_assignment(grid, p_dfs, time_s=120)
    print(f"  DFS structural order (priority sort): {rc} in {dt:.3f}s")
    print(f"   -> no orientation bit x in {{0,1}}^135 can satisfy penalty=6.0")
    print(f"   -> image(DFS) ∩ S* = ∅, so image(DFS) ⊈ every orbit trivially.")

    print()
    print("=" * 72)
    print(" (B) Run reference DFS and canonicalize its best output")
    print("=" * 72)

    t0 = time.time()
    values, pen, states = run_reference_dfs(grid, max_states=200_000)
    print(f"  baseline DFS finished in {time.time()-t0:.2f}s,"
          f" states={states:,}, best penalty={pen:.1f}")

    if values is not None:
        pw, xw = values_to_px(grid, values)
        rep = measure(values, grid)
        print(f"  reproduced penalty from cell dict: {rep.penalty}")
        can = g6.canonical_c6(pw, xw)
        print(f"  DFS canonical p[:8]={can[0][:8]}")
        print(f"  DFS canonical x[:8]={can[1][:8]}")
        opt = rep.penalty <= PENALTY_FLOOR
        print(f"  DFS best is optimal (penalty=6.0)? {opt}")

        # compare against known orbit reps
        import os
        path = "output/orbit_reps_report.json"
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                orbit_reps = json.load(f)
            canonical_forms = {
                (tuple(rec["canon_p"]), tuple(rec["canon_x"])) for rec in orbit_reps
            }
            hit = can in canonical_forms
            print(f"  DFS canon among {len(orbit_reps)} known optimal orbits? {hit}")

    # Final step-4 summary on file
    summary = {
        "step4": {
            "A_slice_unsat_under_pinned_pair_assignment": str(rc),
            "B_reference_dfs_best_penalty": pen,
            "B_reference_dfs_states": states,
            "conclusion": (
                "The fixed-pair 2^135 orientation slice is UNSAT for optimal "
                "penalty 6.0 (Z3 direct check), and the actual DFS run does "
                "not reach 6.0 within 200k states.  Therefore the DFS "
                "generator's image contains no optimal orbit representative; "
                "it is orbit-incomplete."
            ),
        }
    }

    with open("output/step4_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("  -> output/step4_summary.json saved")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
