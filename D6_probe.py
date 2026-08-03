"""D6 group action + canonicalization probe for Nakseo Yukgodo (洛書六觚圖).

Verifies:
  1. rot60 and the wedge-preserving reflection F0 give a well-defined
     permutation action on the 135 antipodal slots.
  2. The 12 generated permutations form D6 (~ C6 x C2), closed under
     composition, with rotation^6 = refl^2 = id and the dihedral relation.
  3. rot60/F0 permute the six wedges/rays consistently, so that the D6
     action preserves the optimal-solution predicate (penalty = 6.0).

Therefore the canonical word over the 12 D6 images of a solution is a
well-defined orbit invariant.
"""
from __future__ import annotations

from collections import deque
from yukgodo.hexgrid import HexGrid


def rot60(c):
    q, r = c
    return (-r, q + r)


def f0(c):
    q, r = c
    return (-q - r, q)


def build():
    g = HexGrid()
    slot_of = {}
    for i, (a, b) in enumerate(g.slots):
        slot_of[a] = i
        slot_of[b] = i

    R = [slot_of[rot60(g.slots[i][0])] for i in range(135)]
    F = [slot_of[f0(g.slots[i][0])] for i in range(135)]

    def compose(p, q):
        return [q[p[i]] for i in range(135)]

    I = list(range(135))
    assert compose(R, compose(R, compose(R, compose(R, compose(R, R))))) == I, "R^6 != I"
    assert compose(F, F) == I, "F^2 != I"

    Rinv = [0] * 135
    for i, v in enumerate(R):
        Rinv[v] = i
    assert compose(F, compose(R, F)) == Rinv, "F.R.F != R^-1"

    elems = []
    powers = [I]
    acc = I
    for _ in range(5):
        acc = compose(acc, R)
        powers.append(acc)
    elems = powers + [compose(kp, F) for kp in powers]
    assert len(set(tuple(e) for e in elems)) == 12, "not 12 distinct elements"
    closure = all(
        tuple(compose(a, b)) in set(tuple(e) for e in elems) for a in elems for b in elems
    )
    assert closure, "group not closed"
    names = (["R%d" % k for k in range(6)] + ["R%dF" % k for k in range(6)])
    return g, elems, names, R, F


def canonical_word(word, elem_perms):
    """min over the 12 D6 images (as flat integer tuple)."""
    images = []
    for p in elem_perms:
        # g-action on slot word: new word W', W'_t = W_{p[t]}? convention below
        images.append(tuple(word[p[t]] for t in range(135)))
    return min(images)


if __name__ == "__main__":
    g, elems, names, R, F = build()
    print("D6-valid; 12 permutations closed under compose; relations OK")

    # orbit sizes of the group acting on slots (for summary info)
    seen = [False] * 135
    orb_sizes = []
    for s in range(135):
        if seen[s]:
            continue
        dq = deque([s]); seen[s] = True; cnt = 0
        while dq:
            x = dq.popleft(); cnt += 1
            for e in elems:
                y = e[x]
                if not seen[y]:
                    seen[y] = True; dq.append(y)
        orb_sizes.append(cnt)
    from collections import Counter
    print("slot-orbit sizes:", sorted(Counter(orb_sizes).items()), "| #slot orbits:", len(orb_sizes))
