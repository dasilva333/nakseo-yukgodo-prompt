"""D6 group action on the hexagonal lattice; orbit canonicalization for
Nakseo Yukgodo (洛書六觚圖).

Mathematical conventions
------------------------
* Axial coords c = (q, r); cube third component s = -q - r.
* The 12-element dihedral group D6 = <rho, sigma> acts on axial coords:
      rho   : (q, r) -> (-r, q + r)     (60-degree CCW rotation)
      sigma : (q, r) -> (q + r, -r)     (mirror across the corner C_0 axis)
  These satisfy rho^6 = sigma^2 = id and  sigma rho sigma = rho^{-1}.

* Each isometry g is a permutation of the 270 filled cells commuting with
  antipode c -> -c, hence acts on the 135 antipodal slots.  A *solution
  word* is a pair (p, x):  p_t in {1..135} is the low value of the
  complementary pair at slot t, x_t in {0,1} says whether slot cell A gets
  the low (x = 0) or the high (x = 1) value.  Then value A = p_t + (271 -
  2 p_t) x_t and value B = 271 - value A.  Every g in D6 induces
      new_p[P_g(t)] = p_t,  new_x[P_g(t)] = x_t XOR flip_g(t),
  where P_g is the slot permutation of g and flip_g(t) records whether or not
  g(A_t) equals the A-cell of the image slot.  The pair (P_g, flip_g) *is*
  the faithful action; it need not be a pure slot permutation because the
  "A cell" parsing of the grid's `slots` list is only a coordinate chart.

* Under each isometry, each geometric structure (sides / wedges / rays /
  axes) is mapped bijectively onto a permutation of its own index set; the
  required label permutations are computed once and cached.  Since every
  optimal-solution predicate is stated purely in terms of these sums, the
  D6 action preserves S* precisely.

* Canonicalization:  `Can(w) = min { g.w : g in D6 }` computed on the
  concatenation (p, x) under lexicographic order.  Theorem (Step 2 of
  PROMPT.md): words A, B are in the same D6 orbit iff Can(A) = Can(B).
"""
from __future__ import annotations

from .hexgrid import HexGrid, PAIR_SUM


# ---------------------------------------------------------------------------
# Isometries (axial representation)
# ---------------------------------------------------------------------------

def rot60(c):
    q, r = c
    return (-r, q + r)


def rot_k(k):
    def f(c):
        x = c
        for _ in range(k):
            x = rot60(x)
        return x
    return f


def refl_main(c):
    """Reflection across the axis through corner C_0 = (9,0); fixes C_0."""
    q, r = c
    return (q + r, -r)


def _build_isometries():
    rots = [rot_k(k) for k in range(6)]
    return rots + [lambda c, k=k: rot_k(k)(refl_main(c)) for k in range(6)]


ISOMETRIES = _build_isometries()
ISOMETRY_NAMES = (
    ["R%d" % k for k in range(6)] + ["R%d*Sigma" % k for k in range(6)]
)


def slot_perm(grid: HexGrid, f):
    """Return (perm, flip) for isometry f acting on the 135 slots.

    perm[t] = slot index of f(slot_t.A)
    flip[t] = 0 if f(slot_t.A) is the A-cell of that slot else 1.

    Together with  new_p[perm[t]] = p_t,  new_x[perm[t]] = x_t XOR flip[t],
    this is the faithful left action of f on solution words.
    """
    slot_of = {}
    for i, (a, b) in enumerate(grid.slots):
        slot_of[a] = i
        slot_of[b] = i
    perm, flip = [], []
    for t, (a, b) in enumerate(grid.slots):
        s = slot_of[f(a)]
        perm.append(s)
        flip.append(0 if f(a) == grid.slots[s][0] else 1)
    return tuple(perm), tuple(flip)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class D6:
    """Precomputed D6 action (slot permutations + orientation flips)."""

    def __init__(self, grid: HexGrid) -> None:
        self.grid = grid
        perms, flips = [], []
        for f in ISOMETRIES:
            P, F = slot_perm(grid, f)
            perms.append(P); flips.append(F)
        self.perms = perms  # 12 slot permutations (with repetition)
        self.flips = flips  # 12 orientation flips
        self.names = ISOMETRY_NAMES

        # structural label permutations per isometry
        self.wedge_maps = [self._struct_perm(grid.wedges, grid.wedge_of, f)
                           for f in ISOMETRIES]
        self.ray_maps = [self._struct_perm(grid.rays, grid.ray_of, f)
                         for f in ISOMETRIES]
        sides_index = {c: tuple(grid.sides_of.get(c, ())) for c in grid.filled}
        self.side_maps = [self._struct_perm_sides(grid.sides, sides_index, f)
                          for f in ISOMETRIES]

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def _struct_perm(lists, index_of, f):
        return tuple(index_of[f(L[0])] for L in lists)

    @staticmethod
    def _struct_perm_sides(lists, sides_index, f):
        out = []
        for L in lists:
            c = f(L[3])  # 4th cell of the side is never a corner
            out.append(sides_index[c][0])
        return tuple(out)

    # -- group action on words -------------------------------------------
    def act_px(self, k: int, pword, xword):
        """Apply D6 element k (k mod 12) to solution words (p, x).

        new_p[P[t]] = p_t;  new_x[P[t]] = x_t XOR flip_k[t].

        NOTE (important for this grid): only elements k = 0..5 (pure
        rotations) are guaranteed to map optimal solutions to optimal
        solutions.  The 45-cell wedge sector is chiral, so the reflections
        (k = 6..11) do not preserve the wedge multisets.  Use
        `orbit_words_c6`/`canonical_c6` for orbit classification on S*.
        """
        n = len(pword)
        P, F = self.perms[k], self.flips[k]
        p2 = [0] * n; x2 = [0] * n
        for t in range(n):
            p2[P[t]] = pword[t]
            x2[P[t]] = xword[t] ^ F[t]
        return tuple(p2), tuple(x2)

    def orbit_words(self, pword, xword):
        """All 12 D6 images of the (p, x) word (usually distinct)."""
        out = {self.act_px(k, pword, xword) for k in range(12)}
        return sorted(out)

    def orbit_words_c6(self, pword, xword):
        """The 6 pure-rotation images (C6 subgroup) of the (p, x) word."""
        return [self.act_px(k, pword, xword) for k in range(6)]

    def canonical_px(self, pword, xword):
        """Lex-min over all 12 D6 images — complete D6-orbit invariant on
        slot words (NOT restricted to optimal solutions; see module docs)."""
        return min(self.orbit_words(pword, xword))

    def canonical_c6(self, pword, xword):
        """Lex-min over the 6 rotation images — the faithful orbit identifier
        on the optimal solution space S*."""
        return min(self.orbit_words_c6(pword, xword))


# ---------------------------------------------------------------------------
# Penalties of an encoded word
# ---------------------------------------------------------------------------

def penalties_for_px(grid: HexGrid, pword, xword):
    """Compute (side_sums, wedge_sums, ray_sums, penalty) for (p, x) words."""
    side = [0] * 6; wedge = [0] * 6; ray = [0] * 6
    for t, (a, b) in enumerate(grid.slots):
        L, H = pword[t], PAIR_SUM - pword[t]
        va, vb = (H, L) if xword[t] else (L, H)
        for m in grid.sides_of.get(a, ()):
            side[m] += va
        for m in grid.sides_of.get(b, ()):
            side[m] += vb
        wedge[grid.wedge_of[a]] += va
        wedge[grid.wedge_of[b]] += vb
        ra = grid.ray_of.get(a, -1); rb = grid.ray_of.get(b, -1)
        if ra >= 0: ray[ra] += va
        if rb >= 0: ray[rb] += vb
    pen = sum(abs(s - 1355) for s in side)
    pen += sum(abs(w - 6097.5) for w in wedge)
    pen += sum(abs(r - 1219.5) for r in ray)
    return side, wedge, ray, pen


__all__ = [
    "ISOMETRIES", "ISOMETRY_NAMES", "D6", "rot60", "refl_main",
    "slot_perm", "penalties_for_px",
]
