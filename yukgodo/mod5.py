"""mod 5 잉여류 채색 시각화 + 5개 층의 기하 관계 전수조사.

최적해(output/solution.json)의 값 v를 v mod 5로 분류해 채색한다:

    잉여 1 = 검정, 잉여 2 = 빨강, 잉여 3 = 파랑, 잉여 4 = 회색, 잉여 0 = 노랑

270칸은 잉여류별로 정확히 54칸씩 5개 층으로 갈라진다(270 = 5×54).
이 모듈은 5개 층을 낱낱이 분리한 뒤 다음을 전수조사한다:

    1. 층 간 D6(6회전 × 2반사 = 12개 육각 대칭) 합동 — 집합 동치 전수
    2. 층 자기대칭(안정화자) — 비자명 대칭원소 전수
    3. networkx 유도 부분그래프 동형(형상 합동) — 시그니처 일치 쌍에 VF2
    4. 고리/섹터/변/광선/축행 분포의 층별 편차 (균일 대비 χ²)
    5. 동류 인접(낮은 차수 응집도)과 층 간 인접 몫행렬(5×5)
    6. 값 이동 사상 T: 위치(v) → 위치(v+5) 의 순환 구조와 보행 거리
    7. 대척점(점대칭)의 잉여류 작용: 합 271 ≡ 1 (mod 5) → r ↦ (1−r) mod 5

실행: python3 -m yukgodo.mod5
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Circle, Polygon

from .hexgrid import CENTER, DIRECTIONS, HexGrid, add, cube, ring_of, to_pixel
from .reverse import load_solution
from .visualize import _setup_cjk_font  # noqa: F401  (폰트 설정 부수효과)

# 잉여류 채색 (사용자 지정)
CLASS_COLORS = {
    1: "#111111",   # 검정
    2: "#d62728",   # 빨강
    3: "#1f5fbf",   # 파랑
    4: "#8c8c8c",   # 회색
    0: "#ffd92f",   # 노랑
}
CLASS_TEXT = {1: "white", 2: "white", 3: "white", 4: "black", 0: "black"}
CLASS_NAMES = {1: "black", 2: "red", 3: "blue", 4: "gray", 0: "yellow"}


# ---------------------------------------------------------------------------
# D6 대칭군 (cube 좌표)
# ---------------------------------------------------------------------------

def _rot60(c: tuple[int, int]) -> tuple[int, int]:
    """60° 반시계 회전: cube (q,r,s) → (−s,−q,−r)."""
    q, r, s = cube(c)
    return (-s, -q)


def _reflect(c: tuple[int, int]) -> tuple[int, int]:
    """q축 고정 반사: cube (q,r,s) → (q,s,r)."""
    q, r, s = cube(c)
    return (q, s)


def build_d6(grid: HexGrid) -> list[tuple[str, object]]:
    """육각 격자의 이면체군 D6 (12개 원소)를 이름과 함께 구성한다."""
    elems = []
    for k in range(6):
        elems.append((f"회전{k * 60}°", _make_pow(_rot60, k)))
        elems.append((f"반사+회전{k * 60}°", _make_pow_ref(k)))
    # 검증: 전부 cell_set의 치환이고 서로 다른 12개여야 함
    images = set()
    for name, g in elems:
        img = frozenset(g(c) for c in grid.cells)
        assert img == grid.cell_set, name
        images.add(frozenset((c, g(c)) for c in grid.cells))
    assert len(images) == 12, "D6 원소가 12개가 아님"
    return elems


def _make_pow(f, k: int):
    def g(c):
        for _ in range(k):
            c = f(c)
        return c
    return g


def _make_pow_ref(k: int):
    def g(c):
        c = _reflect(c)
        for _ in range(k):
            c = _rot60(c)
        return c
    return g


def hex_dist(a: tuple[int, int], b: tuple[int, int]) -> int:
    dq, dr = b[0] - a[0], b[1] - a[1]
    return max(abs(dq), abs(dr), abs(dq + dr))


# ---------------------------------------------------------------------------
# 분석
# ---------------------------------------------------------------------------

def analyze_mod5(values: dict, grid: HexGrid) -> dict:
    classes: dict[int, set] = {r: set() for r in range(5)}
    for c, v in values.items():
        classes[v % 5].add(c)
    assert all(len(s) == 54 for s in classes.values())

    d6 = build_d6(grid)

    # 1. 층 간 D6 합동 (5×4 순서쌍 × 12원소 = 240 전수)
    congruences = []
    for r1 in range(5):
        for r2 in range(5):
            if r1 == r2:
                continue
            for name, g in d6:
                if {g(c) for c in classes[r1]} == classes[r2]:
                    congruences.append({"from": r1, "to": r2, "by": name})

    # 2. 층 자기대칭 (안정화자의 비자명 원소)
    self_sym = {}
    for r in range(5):
        stab = [name for name, g in d6
                if {g(c) for c in classes[r]} == classes[r]]
        self_sym[r] = stab

    # 2b. 쌍별 대척 짝지음 행렬 A[i][j] = i층 셀의 대척점이 j층에 속하는 칸 수
    antipode_pairing = [[0] * 5 for _ in range(5)]
    for c, v in values.items():
        a = (-c[0], -c[1])
        antipode_pairing[v % 5][values[a] % 5] += 1

    # 2c. 모든 순서쌍의 D6 최대 겹침 (정확한 합동 = 54/54)
    pair_overlap = {}
    for r1 in range(5):
        for r2 in range(5):
            if r1 == r2:
                continue
            best = max(
                ((len({g(c) for c in classes[r1]} & classes[r2]), name)
                 for name, g in d6),
                key=lambda t: t[0],
            )
            pair_overlap[f"{r1}→{r2}"] = {"overlap": best[0], "by": best[1]}

    # 3. networkx: 육각 인접 그래프와 층별 유도 부분그래프
    G = nx.Graph()
    G.add_nodes_from(grid.filled)   # 중심 虛一은 값이 없으므로 제외
    for c in grid.filled:
        for d in DIRECTIONS:
            n = add(c, d)
            if n in grid.cell_set and n != CENTER:
                G.add_edge(c, n)
    subs = {r: G.subgraph(classes[r]).copy() for r in range(5)}
    comp = {r: sorted((len(s) for s in nx.connected_components(subs[r])),
                      reverse=True)
            for r in range(5)}
    internal_edges = {r: subs[r].number_of_edges() for r in range(5)}
    # 형상 동형: 시그니처(연결성분 크기열 + 차수열)가 같은 쌍만 VF2
    signatures = {
        r: (tuple(comp[r]), tuple(sorted(dict(subs[r].degree()).values())))
        for r in range(5)
    }
    iso_pairs = []
    for r1 in range(5):
        for r2 in range(r1 + 1, 5):
            if signatures[r1] != signatures[r2]:
                iso_pairs.append({"pair": [r1, r2], "isomorphic": False,
                                  "note": "시그니처 불일치 (VF2 생략)"})
                continue
            gm = nx.algorithms.isomorphism.GraphMatcher(subs[r1], subs[r2])
            iso_pairs.append({"pair": [r1, r2],
                              "isomorphic": gm.is_isomorphic()})

    # 4. 분포: 고리/섹터/변/광선/축행(cube a=0 성분)
    def dists(cells: set) -> dict:
        rings = Counter(ring_of(c) for c in cells)
        wedges = Counter(grid.wedge_of[c] for c in cells)
        sides = Counter(j for c in cells for j in grid.sides_of.get(c, []))
        rays = Counter(grid.ray_of[c] for c in cells if c in grid.ray_of)
        rowsm = Counter(cube(c)[0] for c in cells)
        return {
            "rings": [rings.get(k, 0) for k in range(1, 10)],
            "wedges": [wedges.get(i, 0) for i in range(6)],
            "sides": [sides.get(j, 0) for j in range(6)],
            "rays": [rays.get(i, 0) for i in range(6)],
            "rows": [rowsm.get(m, 0) for m in range(-9, 10)],
        }

    layer_dist = {r: dists(classes[r]) for r in range(5)}

    def chi2(xs: list[float], expects: list[float]) -> float:
        return sum((x - e) ** 2 / e for x, e in zip(xs, expects) if e > 0)

    # 층(54칸 = 전체의 1/5)의 기대 점유: 섹터 45/5=9, 광선 9/5=1.8, 고리 6k/5
    uniformity = {
        r: {
            "wedges_chi2": chi2(layer_dist[r]["wedges"], [9.0] * 6),
            "rays_chi2": chi2(layer_dist[r]["rays"], [1.8] * 6),
            "rings_chi2": chi2(layer_dist[r]["rings"],
                             [6.0 * k / 5 for k in range(1, 10)]),
        }
        for r in range(5)
    }

    # 5. 층 간 인접 몫행렬 M[i][j] = i층-j층 사이 인접 간선 수
    M = [[0] * 5 for _ in range(5)]
    for a, b in G.edges():
        ra, rb = values[a] % 5, values[b] % 5
        M[ra][rb] += 1
        if ra != rb:
            M[rb][ra] += 1

    # 6. 값 이동 사상 T: 위치(v) → 위치(v+5) (mod 270, 값 공간에서)
    pos = {v: c for c, v in values.items()}
    T = {pos[v]: pos[(v + 5 - 1) % 270 + 1] for v in range(1, 271)}
    # 순환 구조
    seen, cycles = set(), []
    for c0 in T:
        if c0 in seen:
            continue
        cyc, c = [], c0
        while c not in seen:
            seen.add(c)
            cyc.append(c)
            c = T[c]
        cycles.append(len(cyc))
    step_dists = Counter(hex_dist(c, T[c]) for c in T)
    # T와 D6 원소의 상관: T(c) == g(c) 인 비율이 최대인 대칭원소
    best_overlap = max(
        ((sum(1 for c in T if T[c] == g(c)), name) for name, g in d6),
        key=lambda t: t[0],
    )

    # 7. 대척점의 잉여류 작용: 합 271 ≡ 1 (mod 5) ⇒ v의 대척점 값 ≡ (1−r) mod 5
    antipode_class = {}
    mismatches = 0
    for c, v in values.items():
        partner = values[(-c[0], -c[1])]
        if (v + partner) % 5 != 1 % 5 or (v + partner) != 271:
            mismatches += 1
    for r in range(5):
        image = frozenset(((-c[0], -c[1])) for c in classes[r])
        antipode_class[r] = next(r2 for r2 in range(5)
                                 if image == classes[r2])

    # 층별 합 (값 공간에서 결정적: r + 5k, k=0..53)
    class_sums = {r: sum(v for v in range(r if r else 5, 271, 5))
                  for r in range(5)}

    return {
        "classes": classes,
        "class_sums": class_sums,
        "congruences": congruences,
        "self_symmetry": self_sym,
        "antipode_pairing": antipode_pairing,
        "pair_overlap": pair_overlap,
        "components": comp,
        "internal_edges": internal_edges,
        "iso_pairs": iso_pairs,
        "layer_dist": layer_dist,
        "uniformity": uniformity,
        "quotient_matrix": M,
        "T_cycles": sorted(cycles, reverse=True),
        "T_step_dists": dict(sorted(step_dists.items())),
        "T_best_d6_overlap": {"by": best_overlap[1], "cells": best_overlap[0]},
        "antipode_class_map": antipode_class,
        "antipode_mismatches": mismatches,
    }


# ---------------------------------------------------------------------------
# 렌더링
# ---------------------------------------------------------------------------

def draw_mod5_coloring(values: dict, grid: HexGrid, path_png: str,
                       path_svg: str | None = None) -> None:
    """전체 도안을 mod 5 잉여류 채색으로 그린다."""
    fig, ax = plt.subplots(figsize=(18, 18))
    ax.set_aspect("equal")
    ax.axis("off")
    size, cell_r = 1.0, 0.46

    for corner in grid.corners():
        x0, y0 = to_pixel(CENTER, size)
        x1, y1 = to_pixel(corner, size)
        ax.plot([x0, x1 * 1.08], [y0, y1 * 1.08], color="#bbbbbb",
                lw=1.2, zorder=1)
    pts = [to_pixel(c, size) for c in grid.corners()]
    ax.add_patch(Polygon([(p[0] * 1.12, p[1] * 1.12) for p in pts],
                         closed=True, fill=False, edgecolor="#333333",
                         lw=2.0, zorder=2))

    for c in grid.filled:
        x, y = to_pixel(c, size)
        r = values[c] % 5
        ax.add_patch(Circle((x, y), cell_r, facecolor=CLASS_COLORS[r],
                            edgecolor="#555555", lw=0.5, zorder=3))
        ax.text(x, y, str(values[c]), ha="center", va="center",
                fontsize=6.5, color=CLASS_TEXT[r], zorder=4)

    x, y = to_pixel(CENTER, size)
    ax.add_patch(Circle((x, y), cell_r, facecolor="white",
                        edgecolor="#c00000", lw=1.6, zorder=3))
    ax.text(x, y, "Empty", ha="center", va="center", fontsize=8,
            color="#c00000", weight="bold", zorder=4)

    handles = [plt.Line2D([0], [0], marker="o", color="w",
                          markerfacecolor=CLASS_COLORS[r], markersize=14,
                          label=f"Residue {r} ({CLASS_NAMES[r]}) — 54 cells")
               for r in (1, 2, 3, 4, 0)]
    ax.legend(handles=handles, loc="upper right", fontsize=13,
              framealpha=0.95)
    ax.set_title("Nakseo Yukgodo (洛書六觚圖) — coloring by residue modulo 5\n"
                 "1 black · 2 red · 3 blue · 4 gray · 0 yellow",
                 fontsize=18, pad=18)
    ax.autoscale_view()
    fig.tight_layout()
    fig.savefig(path_png, dpi=180, bbox_inches="tight")
    if path_svg:
        fig.savefig(path_svg, bbox_inches="tight")
    plt.close(fig)


def draw_mod5_layers(values: dict, classes: dict, class_sums: dict,
                     grid: HexGrid, path_png: str) -> None:
    """5개 층을 각각 분리해 한 장에 그린다 (5장 낱장 분리)."""
    fig, axes = plt.subplots(1, 5, figsize=(30, 8.2))
    size, cell_r = 1.0, 0.46
    for ax, r in zip(axes, (1, 2, 3, 4, 0)):
        ax.set_aspect("equal")
        ax.axis("off")
        pts = [to_pixel(c, size) for c in grid.corners()]
        ax.add_patch(Polygon([(p[0] * 1.12, p[1] * 1.12) for p in pts],
                             closed=True, fill=False, edgecolor="#999999",
                             lw=1.2, zorder=1))
        for c in grid.filled:
            x, y = to_pixel(c, size)
            if c in classes[r]:
                ax.add_patch(Circle((x, y), cell_r, facecolor=CLASS_COLORS[r],
                                    edgecolor="#444444", lw=0.4, zorder=3))
                ax.text(x, y, str(values[c]), ha="center", va="center",
                        fontsize=5.2, color=CLASS_TEXT[r], zorder=4)
            else:
                ax.add_patch(Circle((x, y), cell_r, facecolor="#f2f2f2",
                                    edgecolor="#dddddd", lw=0.3, zorder=2))
        x, y = to_pixel(CENTER, size)
        ax.add_patch(Circle((x, y), cell_r, facecolor="white",
                            edgecolor="#c00000", lw=1.4, zorder=3))
        ax.text(x, y, "Empty", ha="center", va="center", fontsize=6,
                color="#c00000", zorder=4)
        ax.set_title(f"Residue {r} ({CLASS_NAMES[r]})\n54 cells, layer sum {class_sums[r]}",
                     fontsize=15)
        ax.autoscale_view()
    fig.suptitle("Nakseo Yukgodo (洛書六觚圖) mod 5 — five residue layers", fontsize=20)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path_png, dpi=160, bbox_inches="tight")
    plt.close(fig)


def draw_mod5_symmetry(values: dict, classes: dict, grid: HexGrid,
                       path_png: str) -> None:
    """합동 쌍 (2,4), (1,0): 한 층과 다른 층의 대척상(회전180°)을 겹쳐 그린다.

    색칠된 원 = 잉여 r1 층, 속 빈 테두리 원 = 잉여 r2 층의 대척상.
    모든 테두리 원이 색칠된 원 위에 정확히 얹히면 54/54 합동.
    """
    pairs = [(2, 4), (1, 0)]
    fig, axes = plt.subplots(1, 2, figsize=(22, 11))
    size, cell_r = 1.0, 0.46
    for ax, (r1, r2) in zip(axes, pairs):
        ax.set_aspect("equal")
        ax.axis("off")
        pts = [to_pixel(c, size) for c in grid.corners()]
        ax.add_patch(Polygon([(p[0] * 1.12, p[1] * 1.12) for p in pts],
                             closed=True, fill=False, edgecolor="#999999",
                             lw=1.2, zorder=1))
        for c in grid.filled:
            x, y = to_pixel(c, size)
            ax.add_patch(Circle((x, y), cell_r, facecolor="#f2f2f2",
                                edgecolor="#e0e0e0", lw=0.3, zorder=2))
        match = 0
        for c in classes[r1]:
            x, y = to_pixel(c, size)
            ax.add_patch(Circle((x, y), cell_r, facecolor=CLASS_COLORS[r1],
                                edgecolor="#333333", lw=0.5, zorder=3))
            if (-c[0], -c[1]) in classes[r2]:
                match += 1
        for c in classes[r2]:
            x, y = to_pixel((-c[0], -c[1]), size)
            ax.add_patch(Circle((x, y), cell_r * 1.45, fill=False,
                                edgecolor="#000000", lw=1.4, zorder=4))
        ax.set_title(
            f"Residue {r1} ({CLASS_NAMES[r1]}) ● vs. antipodal image of residue "
            f"{r2} ({CLASS_NAMES[r2]}) ○\n"
            f"{match}/54 cells coincide — congruent under 180° rotation", fontsize=16)
        ax.autoscale_view()
    fig.suptitle("Nakseo Yukgodo (洛書六觚圖) mod 5 — central-symmetry congruence of layers\n"
                 "(antipodal-pair sum 271 ⇒ opposite value ≡ 1 − v mod 5)", fontsize=18)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path_png, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 리포트
# ---------------------------------------------------------------------------

def write_mod5_json(a: dict, path: str) -> None:
    out = {k: v for k, v in a.items() if k != "classes"}
    out["classes"] = {r: sorted(list(s)) for r, s in a["classes"].items()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


def write_mod5_markdown(a: dict, path: str) -> None:
    L = []
    L.append("# 洛書六觚圖 mod 5 잉여류 분석\n")
    L.append("값 v를 v mod 5로 분류 (1 검정 · 2 빨강 · 3 파랑 · 4 회색 · 0 노랑).")
    L.append("270칸 = 5류 × 54칸. 층 합: " +
             ", ".join(f"잉여 {r} = {a['class_sums'][r]}" for r in (1, 2, 3, 4, 0)) +
             " (값 공간에서 결정적).\n")

    L.append("## 1. 층 간 D6 합동 전수조사 (240 = 5×4 순서쌍 × 12원소)\n")
    L.append("**합동 쌍: 잉여 2 ↔ 잉여 4, 잉여 1 ↔ 잉여 0 (회전180° = 점대칭).**\n")
    if a["congruences"]:
        L.append("| 층 | → 층 | 대칭원소 |")
        L.append("|---|---|---|")
        for h in a["congruences"]:
            L.append(f"| 잉여 {h['from']} | 잉여 {h['to']} | {h['by']} |")
    else:
        L.append("합동 없음.")
    L.append("")
    L.append("모든 순서쌍의 D6 최대 겹침 (54/54 = 정확한 합동):\n")
    L.append("| 쌍 | 최대 겹침 | 달성 대칭원소 |")
    L.append("|---|---|---|")
    for r1 in range(5):
        for r2 in range(r1 + 1, 5):
            o1 = a["pair_overlap"][f"{r1}→{r2}"]
            o2 = a["pair_overlap"][f"{r2}→{r1}"]
            best = o1 if o1["overlap"] >= o2["overlap"] else o2
            mark = " **(합동)**" if best["overlap"] == 54 else ""
            L.append(f"| 잉여 {r1} ↔ 잉여 {r2} | {best['overlap']}/54 | {best['by']}{mark} |")
    L.append("")

    L.append("## 2. 층 자기대칭 (안정화자)\n")
    L.append("| 층 | 자기대칭 원소 |")
    L.append("|---|---|")
    for r in (1, 2, 3, 4, 0):
        L.append(f"| 잉여 {r} | {', '.join(a['self_symmetry'][r])} |")
    L.append("")

    L.append("## 3. 대척점(점대칭)의 잉여류 작용 — 합 271 ≡ 1 (mod 5)\n")
    L.append("대척쌍 합이 271이므로 잉여류는 r ↦ (1−r) mod 5 로 작용해야 한다.")
    L.append(f"실측 불일치 쌍: **{a['antipode_mismatches']}건** (0이어야 함).\n")
    L.append("| 층 | 대척상 |")
    L.append("|---|---|")
    for r in (1, 2, 3, 4, 0):
        L.append(f"| 잉여 {r} | 잉여 {a['antipode_class_map'][r]} |")
    L.append("")
    L.append("대척 짝지음 행렬 A[i][j] = i층 셀의 대척점이 j층에 속하는 칸 수 "
             "(대각선 외 0이면 층이 닫혀 있음):\n")
    header = "| | " + " | ".join(f"잉여{j}" for j in range(5)) + " |"
    L.append(header)
    L.append("|" + "---|" * 6)
    for i in range(5):
        L.append(f"| 잉여{i} | " + " | ".join(str(x) for x in a["antipode_pairing"][i]) + " |")
    L.append("")
    L.append("해석: A[0][1] = A[1][0] = 54 (0층과 1층이 서로의 대척상),")
    L.append("A[2][4] = A[4][2] = 54 (2층과 4층이 서로의 대척상),")
    L.append("A[3][3] = 54 (3층은 자기 자신의 대척상 — 27개 점대칭 쌍).")
    L.append("이것이 §1의 합동 전부다: 0↔1, 2↔4의 회전180° 합동과 3층의")
    L.append("자기대칭은 대척쌍 합 271의 mod 5 잉여류 작용 r ↦ 1−r 그 자체다.")
    L.append("증명 그림: `mod5_symmetry.png` (색칠 층 vs 상대 층의 대척상 ○ 겹침).")
    L.append("")

    L.append("## 4. 층별 인접 구조 (networkx 유도 부분그래프)\n")
    L.append("| 층 | 남 internal 간선 | 연결성분 크기열 |")
    L.append("|---|---|---|")
    for r in (1, 2, 3, 4, 0):
        L.append(f"| 잉여 {r} | {a['internal_edges'][r]} | {a['components'][r]} |")
    L.append("")
    L.append("형상 동형(그래프 동형) 쌍:")
    for p in a["iso_pairs"]:
        r1, r2 = p["pair"]
        verdict = ("**동형**" if p["isomorphic"] else "비동형")
        note = p.get("note", "VF2 판정")
        L.append(f"- 잉여 {r1} ↔ 잉여 {r2}: {verdict} ({note})")
    L.append("")

    L.append("## 5. 층 간 인접 몫행렬 M[i][j] (i층–j층 인접 간선 수)\n")
    header = "| | " + " | ".join(f"잉여{j}" for j in range(5)) + " |"
    L.append(header)
    L.append("|" + "---|" * 6)
    for i in range(5):
        L.append(f"| 잉여{i} | " + " | ".join(str(x) for x in a["quotient_matrix"][i]) + " |")
    L.append("")

    L.append("## 6. 층별 분포 편차 (균일 대비 χ²)\n")
    L.append("| 층 | 섹터 χ² (기대 9) | 광선 χ² (기대 1.8) | 고리 χ² (기대 1.2k) |")
    L.append("|---|---|---|---|")
    for r in (1, 2, 3, 4, 0):
        u = a["uniformity"][r]
        L.append(f"| 잉여 {r} | {u['wedges_chi2']:.2f} | {u['rays_chi2']:.2f} | {u['rings_chi2']:.2f} |")
    L.append("")

    L.append("## 7. 값 이동 사상 T: 위치(v) → 위치(v+5)\n")
    L.append(f"- 순환 구조: {a['T_cycles']} (54 = 270/5 길이 순환 5개가 정상)")
    L.append(f"- 보행 거리 분포: {a['T_step_dists']}")
    b = a["T_best_d6_overlap"]
    L.append(f"- D6 원소와의 최대 일치: {b['by']} 에서 {b['cells']}/270칸 "
             "(구조적 회전이었다면 270이어야 함)")
    L.append("")

    L.append("## 8. 파생 정리 — mod N 일반화 (기록)\n")
    L.append("**정리.** 값 배치에 위치 대합 π(π² = id)이 있고 모든 쌍의 값 합이")
    L.append("상수 S이면, 임의의 법 m에 대해 π는 mod m 잉여류를")
    L.append("**r ↦ (S − r) mod m**으로 작용한다. 따라서 잉여류 층은 π-대칭으로")
    L.append("서로 합동(궤도 길이 2)이거나 자기 합동(고정점: 2r ≡ S (mod m)의 해)이다.\n")
    L.append("까닭 (4단계):")
    L.append("1. 쌍 조건 v + v′ = S 를 mod m으로 내리면 v′ ≡ S − v — 셀마다 성립.")
    L.append("2. 잉여류 위의 작용은 대합 r ↦ S − r 하나뿐이며, 대합의 궤도는")
    L.append("   길이 2의 쌍 아니면 고정점(2r ≡ S)이다.")
    L.append("3. π가 일대일이고 층 크기가 유한하므로, π(층 r) ⊆ 층 (S−r) 은 곧")
    L.append("   집합 동치다 — 겹침이 근사가 아니라 완전한 이유.")
    L.append("4. 본 도안에서 π는 중심 점대칭 = 회전180°이므로, 층 합동은 격자")
    L.append("   대칭 D6 안에서 실현된다 (§1의 전수조사가 실증).\n")
    L.append("따름정리 (쌍 합의 패리티):")
    L.append("- S가 홀수이면 자기쌍(고정 셀)은 값이 존재할 수 없다 — 본 도안의")
    L.append("  S = 271(홀수)와 중심 虛一이 이에 정합한다.")
    L.append("- S가 짝수이면 고정 셀의 값은 S/2로 강제된다 — 九子角得 중궁의")
    L.append("  중심 23 = 46/2가 실례다.\n")
    L.append("교차 도안 검증 (`python3 -m yukgodo.modn_generalization`, 법 2..9 전수):")
    L.append("")
    L.append("| 도안 | 쌍 합 S | π (위치 대합) | 결과 |")
    L.append("|---|---|---|---|")
    L.append("| 06 洛書六觚圖 (본 최적해) | 271 | 중심 점대칭 (전역 회전180°) | mod 2..9 전부 정확 |")
    L.append("| 02 九子角得 중궁 | 46 | 3×3 중심대칭 | mod 2..9 전부 정확, 자기쌍 23 = S/2 |")
    L.append("| 07 重卦用八圖 가로진 | 65 | 행 내 좌우 반전 (국소) | mod 2..9 전부 정확 |")
    L.append("| 07 侯策用九圖 | ≈73 (불완전) | formation 위치쌍 | 혼합 시 붕괴(외 성분 12건), 합 73인 16쌍만 추리면 정확 |")
    L.append("")
    L.append("侯策用九圖의 사례는 조건의 필요성을 보여준다: 쌍 합이 일정하지 않으면")
    L.append("작용은 r ↦ S−r로 모이지 않고 쌍별 실제 합으로 분해.\n")
    L.append("의의와 한계: 이 성질은 대척쌍 가설을 만족하는 **모든** 해(시드 42")
    L.append("최적해 포함)가 가지므로 원래 배치의 식별력은 없다. 그러나 mod 5 채색은")
    L.append("오자각득(mod5_residue_diagram.py)·하도사오도(5-컬러링 문서) 등")
    L.append("구수략 분석 전반에서 반복 사용된 기법이며, 이 정리는 그 성분-쌍 검산을")
    L.append("임의의 mod N으로 일반화한다. 더 선명한 판본의 실제 도안이 이 대칭을")
    L.append("갖지 않는다면 대척 보수쌍 가설이 기각된다는 의미에서 반증 도구다.")
    L.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------------------

def main() -> None:
    grid = HexGrid()
    values = load_solution()
    a = analyze_mod5(values, grid)

    draw_mod5_coloring(values, grid, "output/mod5_coloring.png",
                       "output/mod5_coloring.svg")
    draw_mod5_layers(values, a["classes"], a["class_sums"], grid,
                     "output/mod5_layers.png")
    draw_mod5_symmetry(values, a["classes"], grid, "output/mod5_symmetry.png")
    write_mod5_json(a, "output/mod5_analysis.json")
    write_mod5_markdown(a, "output/mod5_report.md")

    print("=== mod 5 잉여류 분석 ===")
    print(f"층 크기: 전부 54칸, 층 합: {a['class_sums']}")
    print(f"D6 합동: {len(a['congruences'])}건 → {a['congruences']}")
    print(f"대척 짝지음 행렬: {a['antipode_pairing']}")
    print(f"자기대칭: {a['self_symmetry']}")
    print(f"대척 작용 (불일치 {a['antipode_mismatches']}건): {a['antipode_class_map']}")
    print(f"납 internal 간선: {a['internal_edges']}")
    print(f"연결성분: {a['components']}")
    print(f"동형 쌍: {[(p['pair'], p['isomorphic']) for p in a['iso_pairs']]}")
    print(f"T 순환: {a['T_cycles']}, 보행 분포: {a['T_step_dists']}")
    print(f"T 최대 D6 일치: {a['T_best_d6_overlap']}")
    print("산출물: output/mod5_coloring.png/.svg, output/mod5_layers.png,")
    print("        output/mod5_analysis.json, output/mod5_report.md")


if __name__ == "__main__":
    main()
