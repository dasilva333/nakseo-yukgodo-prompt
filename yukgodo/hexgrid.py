"""Geometric model of the hexagonal lattice (the 六觚 diagram) of the Nakseo Yukgodo (洛書六觚圖).

Structure corresponding to the *Hanshu* 律曆志 passage
"二百七十一枚而成六觚, 爲一握" and Su Lin's 蘇林 commentary
"其表六九五十四, 算中積凡得二百七十一枚":

    - center 1 cell + ring k (k=1..9, 6k cells each) = 271 cells
    - 10 cells per side, 54 cells on the perimeter (outermost ring)
    - the center is left void (虛一) and 270 cells receive values

Coordinates are axial coordinates (q, r); the third cube coordinate is
recovered as s = -q - r. A cell's ring number is max(|q|, |r|, |q+r|).
"""

from __future__ import annotations

import math

RADIUS = 9                                # number of rings from the center to a corner
SIDE = RADIUS + 1                         # points per side = 10
N_CELLS = 3 * RADIUS * (RADIUS + 1) + 1   # 271 (六觚一握)
N_FILLED = N_CELLS - 1                    # 270 (虛一則二百七十數)
PAIR_SUM = N_CELLS                        # complementary pair sum = 271
TOTAL_SUM = N_FILLED * PAIR_SUM // 2      # 1+...+270 = 36585
OUTER_RING = RADIUS                       # perimeter ring number = 9 (周五十四數)

# 6 directional unit vectors (axial, counterclockwise order)
DIRECTIONS: list[tuple[int, int]] = [
    (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)
]

Cell = tuple[int, int]
CENTER: Cell = (0, 0)


def add(a: Cell, b: Cell) -> Cell:
    return (a[0] + b[0], a[1] + b[1])


def scale(d: Cell, k: int) -> Cell:
    return (d[0] * k, d[1] * k)


def ring_of(cell: Cell) -> int:
    """Ring number of a cell (0=center, 9=perimeter)."""
    q, r = cell
    return max(abs(q), abs(r), abs(q + r))


def antipode(cell: Cell) -> Cell:
    """Point-symmetric cell about the center (antipode)."""
    return (-cell[0], -cell[1])


def cube(cell: Cell) -> tuple[int, int, int]:
    q, r = cell
    return (q, r, -q - r)


def to_pixel(cell: Cell, size: float = 1.0) -> tuple[float, float]:
    """Screen coordinates of a pointy-top hexagonal lattice (+y is up)."""
    q, r = cell
    x = size * math.sqrt(3.0) * (q + r / 2.0)
    y = size * 1.5 * r
    return (x, y)


class HexGrid:
    """Hexagonal lattice of radius 9 and its substructures.

    Attributes:
        cells:      all 271 cells (including the center)
        filled:     the 270 cells excluding 虛一
        rings:      rings[k] = list of cells of ring k (any order)
        ring_walk:  ring_walk[k] = traversal order of ring k (starts at a corner)
        rays:       rays[i] = the 9 cells of the ray from the center toward corner i (i=0..5)
        sides:      sides[j] = perimeter side j, 10 cells including corners (j=0..5)
        wedges:     wedges[i] = gu-sector (觚) i; six 45-cell sectors partition the 270 cells (i=0..5)
        axes:       axes[a] = axis a through the center, 19 cells (a=0..2, 中觚)
        slots:      135 antipodal slots, each a (cell, antipode(cell)) pair
    """

    def __init__(self, radius: int = RADIUS) -> None:
        self.radius = radius
        self.cells: list[Cell] = [
            (q, r)
            for q in range(-radius, radius + 1)
            for r in range(-radius, radius + 1)
            if max(abs(q), abs(r), abs(q + r)) <= radius
        ]
        self.cell_set = frozenset(self.cells)
        self.filled: list[Cell] = [c for c in self.cells if c != CENTER]

        self.rings: list[list[Cell]] = [[] for _ in range(radius + 1)]
        for c in self.cells:
            self.rings[ring_of(c)].append(c)

        self.ring_walk: list[list[Cell]] = [self._walk_ring(k) for k in range(radius + 1)]

        # rays: 9 cells extending from the center toward corner direction i
        self.rays: list[list[Cell]] = [
            [scale(DIRECTIONS[i], k) for k in range(1, radius + 1)]
            for i in range(6)
        ]
        self.sides: list[list[Cell]] = [self._side(j) for j in range(6)]
        self.wedges: list[list[Cell]] = [self._wedge(i) for i in range(6)]
        self.axes: list[list[Cell]] = [
            [scale(DIRECTIONS[a], t) for t in range(-radius, radius + 1)]
            for a in range(3)
        ]

        # cell → structure reverse references
        self.wedge_of: dict[Cell, int] = {}
        for i, w in enumerate(self.wedges):
            for c in w:
                self.wedge_of[c] = i
        self.ray_of: dict[Cell, int] = {}
        for i, ry in enumerate(self.rays):
            for c in ry:
                self.ray_of[c] = i
        self.sides_of: dict[Cell, list[int]] = {}
        for j, s in enumerate(self.sides):
            for c in s:
                self.sides_of.setdefault(c, []).append(j)

        # antipodal slots: group the 270 cells into 135 point-symmetric pairs
        seen: set[Cell] = set()
        self.slots: list[tuple[Cell, Cell]] = []
        for c in self.filled:
            if c in seen:
                continue
            a = antipode(c)
            seen.add(c)
            seen.add(a)
            self.slots.append((c, a))

    def _walk_ring(self, k: int) -> list[Cell]:
        """Traverse ring k starting at the corner (direction 4), in direction 0→…→5 order."""
        if k == 0:
            return [CENTER]
        walk: list[Cell] = []
        pos = scale(DIRECTIONS[4], k)
        for j in range(6):
            for _ in range(k):
                walk.append(pos)
                pos = add(pos, DIRECTIONS[j])
        return walk

    def _side(self, j: int) -> list[Cell]:
        """Perimeter side j: 10 cells from corner C_j to the next corner, corners included."""
        corner = scale(DIRECTIONS[(j + 4) % 6], self.radius)
        return [add(corner, scale(DIRECTIONS[j], t)) for t in range(self.radius + 1)]

    def _wedge(self, i: int) -> list[Cell]:
        """Gu-sector (觚) i: the 60° wedge that includes ray i as its clockwise boundary, 45 cells.

        On ring k it occupies k cells (1 cell on ray i + k-1 cells of the
        southern wing); the six sectors partition the 270 cells without
        overlap. The antipode maps into sector (i+3)%6.
        """
        cells: list[Cell] = []
        for k in range(1, self.radius + 1):
            base = scale(DIRECTIONS[i], k)
            step = DIRECTIONS[(i + 2) % 6]
            for t in range(k):
                cells.append(add(base, scale(step, t)))
        return cells

    def rows(self, a: int) -> dict[int, list[Cell]]:
        """Rows perpendicular to axis a: cells whose cube component a is m (m=-9..9).

        The m=0 row is the 中觚 (19 cells); as |m| grows the row has 19-|m| cells.
        """
        rows: dict[int, list[Cell]] = {m: [] for m in range(-self.radius, self.radius + 1)}
        for c in self.cells:
            rows[cube(c)[a]].append(c)
        return rows

    def perimeter_walk(self) -> list[Cell]:
        """Traversal order of the 54 perimeter cells (校計周五十四數)."""
        return self.ring_walk[self.radius]

    def corners(self) -> list[Cell]:
        """The 6 perimeter corners (in direction 0..5 order)."""
        return [scale(DIRECTIONS[i], self.radius) for i in range(6)]
