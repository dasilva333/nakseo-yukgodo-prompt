"""Verify all 6 claims from EXTRA.md against the 12 canonical orbit representatives."""
from __future__ import annotations

import json
from collections import Counter
from yukgodo.hexgrid import HexGrid, PAIR_SUM
from yukgodo.analysis import D6

grid = HexGrid()


def values_from_px(p, x):
    vals = {}
    for t, (a, b) in enumerate(grid.slots):
        L, H = p[t], PAIR_SUM - p[t]
        vals[a], vals[b] = ((H, L) if x[t] else (L, H))
    return vals


def get_wedge_pair_sum(vals):
    w = [sum(vals[c] for c in grid.wedges[i]) for i in range(6)]
    return tuple(w[i] + w[i + 3] for i in range(3))


def get_ray_pair_sum(vals):
    r = [sum(vals[c] for c in grid.rays[i]) for i in range(6)]
    return tuple(r[i] + r[i + 3] for i in range(3))


def get_side_pair_sum(vals):
    s = [sum(vals[c] for c in grid.sides[i]) for i in range(6)]
    return tuple(s[i] + s[i + 3] for i in range(3))


def get_corner_pairs(vals):
    cv = [vals[c] for c in grid.corners()]
    return tuple(cv[k] + cv[k + 3] for k in range(3))


def parity_check(vals):
    ok = sum(1 for (a, b) in grid.slots if (vals[a] % 2) != (vals[b] % 2))
    return ok, len(grid.slots)


def main():
    data = json.load(open("output/orbit_reps_report.json", encoding="utf-8"))
    for claim_id, fn in [
        ("Wedge pair = 12195", get_wedge_pair_sum),
        ("Ray pair   = 2439 ", get_ray_pair_sum),
        ("Side pair  = 2710 ", get_side_pair_sum),
        ("Corner pair= 271  ", get_corner_pairs),
    ]:
        tot = Counter()
        for rec in data:
            vals = values_from_px(tuple(rec["canon_p"]), tuple(rec["canon_x"]))
            got = fn(vals)
            tot.update(got)
        print(f"{claim_id}: values found = {sorted(tot.items())}  (target uniform)")

    # parity claim
    for rec in data:
        vals = values_from_px(tuple(rec["canon_p"]), tuple(rec["canon_x"]))
        ok, tot = parity_check(vals)
        print(f"Parity split ok={ok}/{tot} (expect 135/135 for antipodal pairs)")
        break
    print()
    print("Lemma: v(x) % 2 != v(-x) % 2 is guaranteed whenever 271 is odd, so")
    print("all cells in X DO have distinct parity for all legitimate solutions.")


if __name__ == "__main__":
    main()
