# AGENTS.md — Nakseo Yukgodo Orbit Classification Task

## Project Overview

This repository contains a formal-mathematical AI/agent-readable prompt, a Python/Z3
verification pipeline, and a Lean 4 specification, for analyzing the combinatorial
structure of the Nakseo Yukgodo (洛書六觚圖) puzzle—Choi Seok-jeong's 1700
hexagonal magic configuration from *Gusuryak*.

The primary research goals encoded in `PROMPT.md`:

1. D6 group-action formalization on the 135 antipodal slot pairs of the
   radius-9 hexagonal grid (271 cells, 270 filled, center void).
2. Canonicalization `Can : S -> S` under D6 such that `A,D` are in the
   same orbit iff `Can(A) = Can(B)`.
3. Existence of at least two distinct D6 orbits (constructive witness from Z3).
4. Check whether the deterministic pruning backtracking DFS generator (which
   searches the 2^135 flip slice with a fixed pair assignment) intersects
   every optimal orbit.

## Directory Structure

- `PROMPT.md` —Main task specification
- `GENERATOR.md` — Problem formulation, SMT completeness discussion
- `REQUIREMENTS.md` — Hardware, Lean toolchain, venv guide
- `README.md` — GitHub Pages deployment boilerplate (legacy)
- `z3_solver_spec.py` — Baseline SAT/SMT solver reference + DFS experiment
- `lakefile.toml`, `lean-toolchain`, `NakseoProof/Basic.lean` — Lean 4 spec
- `yukgodo/` — Python package: hex grid geometry, weight, solver primitives
- `D6_probe.py` — Initial D6 permutation/sanity checks
- `enumerate_orbits.py` — Enumerates orbit representatives using the PX model
- `verify_orbits_final.py` — Reliability verification of the final 12 orbits
- `dfs_orbit_proof.py` — Z3 UNSAT for the fixed-pair DFS-only 2^135 slice
- `step4_orbit_incompleteness.py` — Integrated Step 4 proof & DFS comparator
- `generate_orbits.py` / `REPORT.py` — Orbit exploration CLI drivers
- `AGENTS.md` — This file

## Installation & Verification

Follow `REQUIREMENTS.md`. For Windows (PowerShell):

```powershell
$env:PYTHONIOENCODING="utf-8"
.\venv\Scripts\python.exe z3_solver_spec.py --outdir output/experiment
```

For Lean 4:
```powershell
& "$env:USERPROFILE\.elan\bin\lake.exe" build
```

## Technical Design Decisions

- **Hex coordinates:** axial `(q, r)`, with `s = -q - r` implicit.
- **D6 element list:** `D6 = [rho^0 … rho^5, rho^0 sig … rho^5 sig]`,
  with `rho(q,r) = (-r, q + r)` and `sig(q,r) = (q + r, -r)` (fix C0=(9,0)).
- **Slot permutation extraction:** precomputed from grid layout once for each
  of the 12 isometries; stored permutations are faithful even under the A/B
  endpoint choice for slots.commutes with the antipode.
- **Word action:** right action `(p', x')[t] = (p[perm^-1 t],
  x[perm^-1 t] ^ flip[t]).
- **Canonicalization:** lexicographic minimum over all 12.
- **Solver stack:** z3.QF_FD via `z3-solver`, linearized pair constraints with
  `If(flip, high, low)` values.  135 p-vars (Int[1,135], all distinct), 135
  x-vars (Bool).
- **Verification guarantees:** every canonical form is verified to yield an
  optimal solution via direct application to the grid (multiset of structure
  sums unchanged), achieving penalty 6.0.

## Important Caveats

- The 600+ orbit tally from earlier iterations was due to a buggy
  canonicalizer that accepted reflections where they were invalid
  (`canonical_px` originally did not include orientation flips).  It was
  replaced by a strict WhitakerChecker and re-run; only 12 orbits were
  retained and re-validated.
- The DFS generator implemented in pseudo-code only considers an fixed
  orientation-slice with pair assignment `p_t = t+1`; it cannot reach any
  optimal solution because the corresponding SMT system is UNSAT (verified).
  The Lean/Steady theorem `slice_misses_either` encodes this formally.
- All Python code is designed to run on Windows 10/11 with UTF-8 encoding;
  the venv dependencies are preinstalled.

## Final Takeaway Summary for Researchers

1. **The optimal solution space has at least 12 distinct D6 orbits**,
   confirmed by Z3 enumeration and mathematical validation.
2. **The orientation-only DFS generator fails to be orbit-complete**,
   leaving all 12 orbits unhit because it laughs at variable value
   assignments all together (searches only the flip-bit dimension).
3. A corrected complete strategy would need to explore the full 135!·2^135
   space or use D6-orbit equivalence queries on the fly, not just the flip
   slice. This would require `p`-permutations on top of orientations.
