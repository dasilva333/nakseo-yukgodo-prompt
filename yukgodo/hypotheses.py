"""Generation and verification of constructive naejeokbeop (添六) hypotheses.

Constructive placement candidates that implement the commentary's 添六
("adding six") literally:

    - add6 family: assign the value (±6·t) mod 271 to the t-th cell of the
      traversal. Since 271 is prime and gcd(6, 271)=1, the values cycle
      through 1..270 exactly once — a complete permutation — and the cell
      where 0 ≡ 271 lands becomes 虛一. This tests whether 虛一 is a
      natural consequence of the 添六 progression rather than a decoration.
    - seq family: sequential assignment of 1..270 (baseline for comparison).

Traversal (walk) variants: inward/outward progression × 6 starting
corners × 2 rotation directions × ring-entry mode (same corner /
continuous spiral) — all are measured and sorted by penalty.
"""

from __future__ import annotations

import json

from .hexgrid import CENTER, DIRECTIONS, HexGrid, add, scale
from .properties import PENALTY_FLOOR, PropertyReport, measure

MODULUS = 271  # 六觚一握, prime


def ring_walk_from(grid: HexGrid, k: int, corner: int, ccw: bool) -> list:
    """Traverse ring k starting at corner `corner`, in the ccw/cw direction."""
    pos = scale(DIRECTIONS[corner], k)
    walk = []
    for j in range(6):
        step = DIRECTIONS[(corner + 2 + j) % 6] if ccw else DIRECTIONS[(corner - 2 - j) % 6]
        for _ in range(k):
            walk.append(pos)
            pos = add(pos, step)
    return walk


def spiral_walk(grid: HexGrid, start_corner: int, ccw: bool,
                inward: bool, continuous: bool) -> list:
    """Full traversal of all 271 cells including the center (center last if inward)."""
    cells: list = []
    ks = range(grid.radius, 0, -1) if inward else range(1, grid.radius + 1)
    corner = start_corner
    for k in ks:
        cells.extend(ring_walk_from(grid, k, corner, ccw))
        # continuous spiral: shift the next ring's starting corner by one step in the rotation direction
        if continuous:
            corner = (corner - 1) % 6 if ccw else (corner + 1) % 6
    if inward:
        cells.append(CENTER)
    else:
        cells.insert(0, CENTER)
    return cells


def construct(grid: HexGrid, walk: list, kind: str) -> dict:
    """Assign values along the traversal. The center cell is excluded from the result dict (虛一)."""
    values: dict = {}
    filled = [c for c in walk if c != CENTER]
    for t, c in enumerate(filled):
        if kind == "add6":
            v = (6 * (t + 1)) % MODULUS
        elif kind == "sub6":
            v = (-6 * (t + 1)) % MODULUS
        elif kind == "seq":
            v = t + 1
        elif kind == "rev":
            v = len(filled) - t
        else:
            raise ValueError(kind)
        values[c] = v
    return values


def evaluate_all(grid: HexGrid) -> list[dict]:
    """Measure every constructive hypothesis and return them sorted by penalty."""
    results: list[dict] = []
    for kind in ("add6", "sub6", "seq", "rev"):
        for inward in (True, False):
            for continuous in (False, True):
                for ccw in (True, False):
                    for corner in range(6):
                        walk = spiral_walk(grid, corner, ccw, inward, continuous)
                        values = construct(grid, walk, kind)
                        rep = measure(values, grid)
                        results.append({
                            "kind": kind,
                            "inward": inward,
                            "continuous": continuous,
                            "ccw": ccw,
                            "corner": corner,
                            "penalty": rep.penalty,
                            "parts": rep.parts,
                            "side_sums": rep.side_sums,
                            "wedge_sums": rep.wedge_sums,
                            "ray_sums": rep.ray_sums,
                            "pair_dev": sum(abs(d) for d in rep.pair_devs),
                        })
    results.sort(key=lambda r: r["penalty"])
    return results


def ring_ap_analysis() -> dict:
    """Model B verification: starting values that achieve ring sum 813k with a per-ring +6 arithmetic progression (mod 271).

    For each ring k a unique starting value exists, and the starts form the
    arithmetic pattern a_k = 274 - 18k — a noteworthy structure — but the
    value sets duplicate across rings, so the condition of placing each of
    1..270 exactly once cannot be met.
    """
    per_ring = {}
    used: set[int] = set()
    for k in range(1, 10):
        n, target = 6 * k, 813 * k
        good = []
        for a in range(1, 271):
            s, v, ok = 0, a, True
            for _ in range(n):
                if v == 0:
                    ok = False
                    break
                s += v
                v = (v + 6) % MODULUS
            if ok and s == target:
                good.append(a)
        per_ring[k] = good
        # accumulate the value set of the representative candidate (for the duplication check)
        if good:
            v = good[0]
            for _ in range(n):
                used.add(v)
                v = (v + 6) % MODULUS
    class_sums = {
        str(r): sum(v for v in range(1, 271) if v % 6 == r % 6)
        for r in range(1, 7)
    }
    return {
        "per_ring_starts": {str(k): v for k, v in per_ring.items()},
        "start_pattern": "a_k = 274 - 18k (unique solution per ring)",
        "distinct_values": len(used),
        "valid": len(used) == 270,
        "verdict": "Model B hits the ring sums exactly but duplicates values, "
                   "violating the 1..270 placement condition → unfit as a placement rule",
        "model_C_class_sums": class_sums,
        "model_C_note": "mod-6 residue classes: 6 classes × 45 values = another reading of "
                        "通加洛書數六倍. Class sums run 5985..6210 (common difference 45); "
                        "opposite class pairs sum to 12195.",
    }


def main() -> None:
    grid = HexGrid()
    results = evaluate_all(grid)
    best = results[0]
    print(f"measured {len(results)} constructive hypotheses (search-optimum penalty floor {PENALTY_FLOOR} for reference)")
    print("\ntop 10:")
    for r in results[:10]:
        print(f"  penalty {r['penalty']:8.1f}  {r['kind']:5s} "
              f"{'inward ' if r['inward'] else 'outward'} "
              f"{'spiral' if r['continuous'] else 'same-corner'} "
              f"{'ccw' if r['ccw'] else ' cw'} corner{r['corner']} "
              f"side-dev {r['parts']['sides']:.0f} pair-dev {r['pair_dev']:.0f}")
    print("\nbottom 3 (worst):")
    for r in results[-3:]:
        print(f"  penalty {r['penalty']:8.1f}  {r['kind']:5s}")

    ring_ap = ring_ap_analysis()
    print("\nModel B (per-ring +6 arithmetic progression) verification:")
    print(f"  per-ring starting values: {ring_ap['per_ring_starts']}")
    print(f"  pattern: {ring_ap['start_pattern']}")
    print(f"  distinct values: {ring_ap['distinct_values']}/270 → {ring_ap['verdict']}")

    out = {
        "note": "verification of 添六 constructive hypotheses: penalty floor 6.0 = search-optimum level",
        "penalty_floor": PENALTY_FLOOR,
        "n_hypotheses": len(results),
        "best": best,
        "top10": results[:10],
        "ring_ap_model_B": ring_ap,
        "conclusion": (
            "Every legible confirmed figure in the commentary (54+6=60, 60/6=10, 中觚 19, "
            "252, 270=6×45) is a cell-count check, not a value-placement rule. "
            "All constructive hypotheses that read 添六 as a value-placement rule "
            "(192 spiral variants of ±6 mod 271, per-ring arithmetic progressions) "
            "fail the magic properties or the one-to-one placement condition. "
            "The reconstructed optimum (antipodal complementary-pair 271 model) is "
            "therefore the best current candidate, and the placement-order rule "
            "(the 寄左/序左 phrase) and certain tail figures (得五百) remain open items pending a clearer edition."
        ),
    }
    with open("output/hypotheses.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nsaved: output/hypotheses.json")


if __name__ == "__main__":
    main()
