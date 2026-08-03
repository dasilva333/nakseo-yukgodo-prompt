"""Rendering of the Nakseo Yukgodo (洛書六觚圖) diagram and property dashboard."""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Polygon

from .hexgrid import CENTER, HexGrid, ring_of, to_pixel
from .properties import PropertyReport, ring_target


def _setup_cjk_font() -> None:
    """Set a font fallback chain so English text uses the default font while Hanja glyphs still render."""
    available = {f.name for f in font_manager.fontManager.ttflist}
    chain = [name for name in (
        "DejaVu Sans", "Droid Sans Fallback", "Droid Sans Japanese",
        "NanumMyeongjo", "NanumGothic", "NanumBarunGothic",
    ) if name in available]
    if chain:
        matplotlib.rcParams["font.family"] = chain
    matplotlib.rcParams["axes.unicode_minus"] = False


_setup_cjk_font()

RING_COLORS = [
    "#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6",
    "#4292c6", "#2171b5", "#08519c", "#08306b", "#041f45",
]
WEDGE_COLORS = [
    "#fdd0a2", "#fdae6b", "#fd8d3c", "#e6550d", "#a63603", "#7f2704",
]


def draw_figure(values: dict, grid: HexGrid, path_png: str,
                path_svg: str | None = None, color_by: str = "ring",
                title: str = "Nakseo Yukgodo (洛書六觚圖) — reconstructed optimum") -> None:
    """Draw the 270-cell placement. The center is left void (虛一)."""
    fig, ax = plt.subplots(figsize=(18, 18))
    ax.set_aspect("equal")
    ax.axis("off")

    size = 1.0
    cell_r = 0.46 * size

    # sector boundary lines (center → 6 corners)
    for corner in grid.corners():
        x0, y0 = to_pixel(CENTER, size)
        x1, y1 = to_pixel(corner, size)
        ax.plot([x0, x1 * 1.08], [y0, y1 * 1.08], color="#bbbbbb",
                lw=1.2, zorder=1)

    # perimeter hexagon outline
    pts = [to_pixel(c, size) for c in grid.corners()]
    cx = [p[0] * 1.12 for p in pts]
    cy = [p[1] * 1.12 for p in pts]
    ax.add_patch(Polygon(list(zip(cx, cy)), closed=True, fill=False,
                         edgecolor="#333333", lw=2.0, zorder=2))

    for c in grid.filled:
        x, y = to_pixel(c, size)
        k = ring_of(c)
        if color_by == "wedge":
            face = WEDGE_COLORS[grid.wedge_of[c]]
            text_color = "white"
        else:
            face = RING_COLORS[k]
            text_color = "white" if k >= 5 else "#1a1a1a"
        ax.add_patch(Circle((x, y), cell_r, facecolor=face,
                            edgecolor="#555555", lw=0.5, zorder=3))
        ax.text(x, y, str(values[c]), ha="center", va="center",
                fontsize=6.5, color=text_color, zorder=4)

    # center 虛一
    x, y = to_pixel(CENTER, size)
    ax.add_patch(Circle((x, y), cell_r, facecolor="white",
                        edgecolor="#c00000", lw=1.6, zorder=3))
    ax.text(x, y, "Empty", ha="center", va="center", fontsize=8,
            color="#c00000", weight="bold", zorder=4)

    ax.set_title(title, fontsize=20, pad=18)
    ax.autoscale_view()
    fig.tight_layout()
    fig.savefig(path_png, dpi=180, bbox_inches="tight")
    if path_svg:
        fig.savefig(path_svg, bbox_inches="tight")
    plt.close(fig)


def draw_dashboard(report: PropertyReport, grid: HexGrid,
                   path_png: str) -> None:
    """Dashboard of property achievement against the targets."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Nakseo Yukgodo (洛書六觚圖) property analysis — targets vs. measured", fontsize=16)

    ax = axes[0][0]
    ax.bar(range(6), report.side_sums, color="#4292c6")
    ax.axhline(1355, color="#c00000", ls="--", lw=1.2, label="target 1355")
    ax.set_title("Six side sums (校計周五十四數)")
    ax.set_xticks(range(6))
    ax.set_xticklabels([f"side {i}" for i in range(6)])
    ax.legend()

    ax = axes[0][1]
    ax.bar(range(6), report.wedge_sums, color="#fd8d3c")
    ax.axhline(6097.5, color="#c00000", ls="--", lw=1.2, label="target 6097.5")
    ax.set_title("Six gu-sector sums")
    ax.set_xticks(range(6))
    ax.set_xticklabels([f"gu {i}" for i in range(6)])
    ax.legend()

    ax = axes[1][0]
    ax.bar(range(6), report.ray_sums, color="#74c476")
    ax.axhline(1219.5, color="#c00000", ls="--", lw=1.2, label="target 1219.5")
    ax.set_title("Six ray sums")
    ax.set_xticks(range(6))
    ax.set_xticklabels([f"ray {i}" for i in range(6)])
    ax.legend()

    ax = axes[1][1]
    ks = list(range(1, grid.radius + 1))
    got = report.ring_sums[1:]
    want = [ring_target(k) for k in ks]
    x = list(range(len(ks)))
    ax.bar([i - 0.2 for i in x], want, width=0.4, color="#bdbdbd",
           label="target 813k")
    ax.bar([i + 0.2 for i in x], got, width=0.4, color="#807dba",
           label="measured")
    ax.set_title("Ring sums (通加洛書數六倍)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"ring {k}" for k in ks])
    ax.legend()

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
