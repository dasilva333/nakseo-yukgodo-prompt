"""Placement search engine for the Nakseo Yukgodo (洛書六觚圖).

Search space:
    The 270 cells are grouped into 135 antipodal slots (point-symmetric
    pairs); each slot is assigned one complementary pair (i, 271-i) and an
    orientation (which side gets the larger number). This representation
    satisfies the following structurally, with no search:

        - antipodal pair sum 271            (the complementary structure of
                                             虛一·共積二百七十)
        - ring k sum = 813k                 (the per-ring distribution of
                                             通加洛書數六倍)
        - axis (中觚) sum = 2439            (十九爲中觚數也)

    Only the remaining goals — side sums equal at 1355 and the half-cell
    balance of sectors and rays — form the search objective.

Method:
    1. start from a constructive seed (spiral-order assignment) and random seeds
    2. simulated annealing (flip / pair-swap / swap+flip moves)
    3. greedy polish
    4. pick the best over multiple restarts
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .hexgrid import PAIR_SUM, HexGrid
from .properties import (
    PENALTY_FLOOR,
    RAY_TARGET,
    SIDE_TARGET,
    WEDGE_TARGET,
)

N_SLOTS = 135


@dataclass
class SolveResult:
    values: dict[tuple[int, int], int]
    penalty: float
    restart_penalties: list[float] = field(default_factory=list)
    iterations: int = 0


class _State:
    """Slot-level state with incremental updates of the structure sums."""

    def __init__(self, grid: HexGrid) -> None:
        self.grid = grid
        self.cell_index = {c: i for i, c in enumerate(grid.filled)}
        self.slots = [
            (self.cell_index[a], self.cell_index[b]) for a, b in grid.slots
        ]
        # cell → structure membership: (list of sides, sector, ray or -1)
        self.side_mem: list[tuple[int, ...]] = []
        self.wedge_mem: list[int] = []
        self.ray_mem: list[int] = []
        for c in grid.filled:
            self.side_mem.append(tuple(grid.sides_of.get(c, ())))
            self.wedge_mem.append(grid.wedge_of[c])
            self.ray_mem.append(grid.ray_of.get(c, -1))
        self.val = [0] * len(grid.filled)
        self.side_sum = [0] * 6
        self.wedge_sum = [0] * 6
        self.ray_sum = [0] * 6

    def set_slot(self, s: int, small: int, flip: bool) -> None:
        ca, cb = self.slots[s]
        large = PAIR_SUM - small
        a, b = (large, small) if flip else (small, large)
        self.val[ca] = a
        self.val[cb] = b
        for arr, mem in (
            (self.side_sum, self.side_mem),
            (self.wedge_sum, self.wedge_mem),
            (self.ray_sum, self.ray_mem),
        ):
            for ci, v in ((ca, a), (cb, b)):
                if arr is self.side_sum:
                    for m in mem[ci]:
                        arr[m] += v
                elif arr is self.ray_sum:
                    if mem[ci] >= 0:
                        arr[mem[ci]] += v
                else:
                    arr[mem[ci]] += v

    def penalty(self) -> float:
        p = 0.0
        for x in self.side_sum:
            p += abs(x - SIDE_TARGET)
        for x in self.wedge_sum:
            p += abs(x - WEDGE_TARGET)
        for x in self.ray_sum:
            p += abs(x - RAY_TARGET)
        return p

    def _apply_delta(self, ci: int, d: int) -> None:
        for m in self.side_mem[ci]:
            self.side_sum[m] += d
        self.wedge_sum[self.wedge_mem[ci]] += d
        r = self.ray_mem[ci]
        if r >= 0:
            self.ray_sum[r] += d

    def do_flip(self, s: int) -> None:
        ca, cb = self.slots[s]
        d = self.val[cb] - self.val[ca]
        self._apply_delta(ca, d)
        self._apply_delta(cb, -d)
        self.val[ca], self.val[cb] = self.val[cb], self.val[ca]

    def do_swap(self, s1: int, s2: int, flip_s2: bool = False) -> None:
        """Exchange the complementary pairs of two slots; flip_s2 also flips one orientation."""
        a1, b1 = self.slots[s1]
        a2, b2 = self.slots[s2]
        va1, vb1, va2, vb2 = self.val[a1], self.val[b1], self.val[a2], self.val[b2]
        na1, nb1 = (vb2, va2) if flip_s2 else (va2, vb2)
        na2, nb2 = (vb1, va1) if flip_s2 else (va1, vb1)
        self._apply_delta(a1, na1 - va1)
        self._apply_delta(b1, nb1 - vb1)
        self._apply_delta(a2, na2 - va2)
        self._apply_delta(b2, nb2 - vb2)
        self.val[a1], self.val[b1] = na1, nb1
        self.val[a2], self.val[b2] = na2, nb2

    def recompute_sums(self) -> None:
        """Recompute all structure sums from the val array."""
        self.side_sum = [0] * 6
        self.wedge_sum = [0] * 6
        self.ray_sum = [0] * 6
        for ci, v in enumerate(self.val):
            self._apply_delta(ci, v)

    def to_values(self) -> dict[tuple[int, int], int]:
        return {c: self.val[i] for c, i in self.cell_index.items()}


def _seed_spiral(state: _State) -> None:
    """Constructive seed: traverse the rings inward from the perimeter in a spiral, assigning complementary pairs in order."""
    grid = state.grid
    slot_of: dict[tuple[int, int], int] = {}
    for s, (a, b) in enumerate(grid.slots):
        slot_of[a] = s
        slot_of[b] = s
    seen: set[tuple[int, int]] = set()
    order: list[int] = []
    for k in range(grid.radius, 0, -1):
        for c in grid.ring_walk[k]:
            if c in seen:
                continue
            seen.add(c)
            seen.add((-c[0], -c[1]))
            order.append(slot_of[c])
    for s, slot_s in enumerate(order):
        state.set_slot(slot_s, s + 1, flip=(s % 2 == 1))


def _seed_random(state: _State, rng: random.Random) -> None:
    pairs = list(range(1, N_SLOTS + 1))
    rng.shuffle(pairs)
    for s in range(N_SLOTS):
        state.set_slot(s, pairs[s], flip=rng.random() < 0.5)


def _anneal(state: _State, rng: random.Random, iterations: int,
            t0: float = 40.0, t1: float = 0.05) -> float:
    n = len(state.slots)
    cur = state.penalty()
    best = cur
    best_snapshot = list(state.val)
    ratio = math.log(t1 / t0)
    for it in range(iterations):
        if cur <= PENALTY_FLOOR:
            break
        t = t0 * math.exp(ratio * it / iterations)
        move = rng.random()
        if move < 0.4:
            s = rng.randrange(n)
            state.do_flip(s)
            new = state.penalty()
            if new <= cur or rng.random() < math.exp(-(new - cur) / t):
                cur = new
            else:
                state.do_flip(s)  # revert
        else:
            s1 = rng.randrange(n)
            s2 = rng.randrange(n)
            if s1 == s2:
                continue
            flip = move >= 0.7
            state.do_swap(s1, s2, flip)
            new = state.penalty()
            if new <= cur or rng.random() < math.exp(-(new - cur) / t):
                cur = new
            else:
                state.do_swap(s1, s2, flip)  # revert (inverse of the same operation)
        if cur < best:
            best = cur
            best_snapshot = list(state.val)
    state.val[:] = best_snapshot
    state.recompute_sums()
    return best


def _polish(state: _State, rng: random.Random, max_rounds: int = 40) -> float:
    """Greedy flip/swap search until no further improvement."""
    n = len(state.slots)
    cur = state.penalty()
    for _ in range(max_rounds):
        improved = False
        order = list(range(n))
        rng.shuffle(order)
        for s in order:
            state.do_flip(s)
            new = state.penalty()
            if new < cur:
                cur = new
                improved = True
            else:
                state.do_flip(s)
        for _ in range(4 * n):
            s1 = rng.randrange(n)
            s2 = rng.randrange(n)
            if s1 == s2:
                continue
            state.do_swap(s1, s2)
            new = state.penalty()
            if new < cur:
                cur = new
                improved = True
            else:
                state.do_swap(s1, s2)
        if cur <= PENALTY_FLOOR or not improved:
            break
    return cur


def solve(grid: HexGrid, iterations: int = 150_000, restarts: int = 8,
          seed: int = 1715) -> SolveResult:
    """Find the optimal placement with multi-restart annealing."""
    rng = random.Random(seed)
    best_values: dict[tuple[int, int], int] | None = None
    best_pen = math.inf
    restart_pens: list[float] = []
    for r in range(restarts):
        state = _State(grid)
        if r == 0:
            _seed_spiral(state)
        else:
            _seed_random(state, rng)
        pen = _anneal(state, rng, iterations)
        pen = _polish(state, rng)
        restart_pens.append(pen)
        if pen < best_pen:
            best_pen = pen
            best_values = state.to_values()
        if best_pen <= PENALTY_FLOOR:
            break
    assert best_values is not None
    return SolveResult(
        values=best_values,
        penalty=best_pen,
        restart_penalties=restart_pens,
        iterations=iterations,
    )
