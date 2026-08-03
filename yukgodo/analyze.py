"""Property analysis of the optimum and report generation.

Organizes the measurements into JSON/Markdown, cross-checking each figure
against the commentary OCR phrases and the 六觚 record of the
*Hanshu* 律曆志.
"""

from __future__ import annotations

import json

from .hexgrid import PAIR_SUM, TOTAL_SUM, HexGrid
from .properties import PropertyReport, ring_target

# Cross-reference table: OCR phrase ↔ verified figure
OCR_ANCHORS = [
    ("共積二百七十", "270 cells are filled", "270 cells (center excluded by 虛一)"),
    ("虛一則二百七十數", "voiding the one leaves 270 numbers", "center cell unused"),
    ("校計周五十四數", "counting the perimeter gives 54", "outermost ring has 54 cells"),
    ("通加洛書數六倍", "six times the Luoshu number (1+..+9=45) = 270", "total cells = 6×45"),
    ("十九爲中觚數也", "the central row has 19", "中觚 (row through the center) has 19 cells"),
    ("置外周添六", "proceeds around the outer ring adding six", "ring k has 6k cells (6,12,...,54)"),
    ("之數見甲編數器章", "provenance note for the numbers", "values 1..270 (籌數略 system)"),
]


def build_analysis(values: dict, grid: HexGrid, report: PropertyReport,
                   penalty_floor: float) -> dict:
    """Build the full analysis as a JSON-serializable dict."""
    corners = grid.corners()
    corner_vals = report.corner_values
    perimeter = [(c, values[c]) for c in grid.perimeter_walk()]
    ring_walk_values = {
        k: [values[c] for c in grid.ring_walk[k]]
        for k in range(1, grid.radius + 1)
    }
    pairs = sorted(
        (min(values[a], values[b]), max(values[a], values[b]))
        for a, b in grid.slots
    )
    mid_rows = {}
    for a in range(3):
        rows = grid.rows(a)
        mid_rows[a] = {
            "cells": len(rows[0]),
            "sum": sum(values.get(c, 0) for c in rows[0]),
        }
    return {
        "meta": {
            "filled_cells": len(values),
            "pair_sum": PAIR_SUM,
            "total_sum": sum(values.values()),
            "total_sum_target": TOTAL_SUM,
            "penalty": report.penalty,
            "penalty_floor": penalty_floor,
            "penalty_parts": report.parts,
        },
        "rings": {
            str(k): {"cells": 6 * k, "sum": report.ring_sums[k],
                     "target": ring_target(k)}
            for k in range(1, grid.radius + 1)
        },
        "sides": {"sums": report.side_sums, "target": 5 * PAIR_SUM},
        "wedges": {"sums": report.wedge_sums, "target": 45 * PAIR_SUM / 2},
        "rays": {"sums": report.ray_sums, "target": 9 * PAIR_SUM / 2},
        "axes": {"sums": report.axis_sums, "target": 9 * PAIR_SUM},
        "middle_rows_中觚": mid_rows,
        "corners": {
            "values": corner_vals,
            "mod9": [v % 9 for v in corner_vals],
            "mod6": [v % 6 for v in corner_vals],
            "note": "for Luoshu cross-check: mod-9 and mod-6 residues of the corner values",
        },
        "pair_check": {
            "all_pairs_sum_271": all(a + b == PAIR_SUM for a, b in pairs),
            "n_pairs": len(pairs),
        },
        "perimeter_sequence": [v for _, v in perimeter],
        "ring_walk_sequences": {str(k): v for k, v in ring_walk_values.items()},
    }


def write_markdown(analysis: dict, report: PropertyReport,
                   path: str, solver_meta: dict) -> None:
    """Save the property analysis report as Markdown."""
    m = analysis["meta"]
    lines: list[str] = []
    lines.append("# Nakseo Yukgodo (洛書六觚圖) reconstructed optimum — property analysis\n")
    lines.append("## 1. Search result summary\n")
    lines.append(f"- seed: {solver_meta.get('seed')}, restarts: {solver_meta.get('restarts')}, "
                 f"iterations per restart: {solver_meta.get('iterations'):,}")
    lines.append(f"- restart penalties: {solver_meta.get('restart_penalties')}")
    lines.append(f"- final penalty: **{m['penalty']}** (theoretical floor {m['penalty_floor']})")
    lines.append(f"- penalty breakdown: {m['penalty_parts']}")
    lines.append("")
    lines.append("## 2. Cross-check against the commentary OCR\n")
    lines.append("| Commentary phrase | Meaning | Check in the reconstructed diagram |")
    lines.append("|---|---|---|")
    for phrase, meaning, check in OCR_ANCHORS:
        lines.append(f"| {phrase} | {meaning} | {check} |")
    lines.append("")
    lines.append("## 3. Basic validation\n")
    lines.append(f"- filled cells: {m['filled_cells']} (target 270)")
    lines.append(f"- grand total: {m['total_sum']} (target {m['total_sum_target']})")
    lines.append(f"- all antipodal pairs (sum 271) hold: {analysis['pair_check']['all_pairs_sum_271']} "
                 f"({analysis['pair_check']['n_pairs']} pairs)")
    lines.append("")
    lines.append("## 4. Sums by structure\n")
    lines.append("### Rings (通加洛書數六倍)\n")
    lines.append("| ring k | cells 6k | sum | target 813k | met |")
    lines.append("|---|---|---|---|---|")
    for k in range(1, 10):
        r = analysis["rings"][str(k)]
        ok = "✓" if r["sum"] == r["target"] else "✗"
        lines.append(f"| {k} | {r['cells']} | {r['sum']} | {r['target']} | {ok} |")
    lines.append("")
    s = analysis["sides"]
    lines.append(f"### Six perimeter sides (target {s['target']} each)\n")
    lines.append(f"- measured: {s['sums']}")
    lines.append("")
    w = analysis["wedges"]
    lines.append(f"### Six gu-sectors (觚) (target {w['target']} each, ideal distribution 6097/6098)\n")
    lines.append(f"- measured: {w['sums']}")
    lines.append("")
    ry = analysis["rays"]
    lines.append(f"### Six rays (target {ry['target']} each, ideal distribution 1219/1220)\n")
    lines.append(f"- measured: {ry['sums']}")
    lines.append("")
    ax = analysis["axes"]
    lines.append(f"### Three axes / 中觚 (target {ax['target']} each)\n")
    lines.append(f"- measured axis sums: {ax['sums']}")
    for a, mr in analysis["middle_rows_中觚"].items():
        lines.append(f"- 中觚 (direction {a}): {mr['cells']} cells, sum {mr['sum']}")
    lines.append("")
    c = analysis["corners"]
    lines.append("## 5. Corner values (for Luoshu cross-check)\n")
    lines.append(f"- values: {c['values']}")
    lines.append(f"- mod 9: {c['mod9']}")
    lines.append(f"- mod 6: {c['mod6']}")
    lines.append("")
    lines.append("## 6. Perimeter traversal sequence (for algorithm-pattern review)\n")
    seq = analysis["perimeter_sequence"]
    lines.append(f"- 54 values: {seq}")
    diffs = [(seq[(i + 1) % 54] - seq[i]) % 270 for i in range(54)]
    lines.append(f"- adjacent differences (clockwise, mod 270): {diffs}")
    lines.append("")
    lines.append("## 7. Interpretation notes\n")
    lines.append("- This placement is a **search optimum** under the 虛一 + antipodal")
    lines.append("  complementary-pair (sum 271) hypothesis; it does not replay the commentary's")
    lines.append("  naejeokbeop procedure but reverse-engineers a placement satisfying its numeric conditions.")
    lines.append("- Ring sums 813k, axis sums 2439, and pair sums 271 are structural consequences of the")
    lines.append("  hypothesis; side 1355, sector 6097/6098, and ray 1219/1220 balances are search-only goals.")
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_json(analysis: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
