"""Probe alternative wedge definitions setwise-closed under D6."""
from yukgodo.hexgrid import HexGrid, DIRECTIONS, scale, add
from yukgodo.analysis import refl_main, rot_k

g = HexGrid()

# Alternative wedge def: cells in sector i are exactly the 45 cells whose
# closest direction to the origin is DIRECTIONS[i]; equivalently, for cell
# c != (0,0), the sector is the cube-coordinate argmax.
def cube(c):
    q, r = c
    return (q, r, -q-r)

def alt_wedge(c):
    """Sector of a cell by cube max-coord with ties on rays assigned CW.
    The cube-coords of the six corners in direction i are:
        dir 0: (+, 0, -)   ray 0 cells x>0, r=0, s=-x
        dir 1: (0, +, -)   ray 1 cells (q=0, r>0)
        dir 2: (-, +, 0)
        dir 3: (-, 0, +)
        dir 4: (0, -, +)
        dir 5: (+, -, 0)
    Sector i: the 45 cells whose cube major axis is i, with ties broken
    CCW-with-ray-i-included.
    """
    q, r, s = cube(c)
    m = max(q, r, s)
    # primary sector by argmax
    candidates = [i for i, v in enumerate((q, r, s)) if v == m]
    if len(candidates) == 1:
        return candidates[0]
    # tie: prefer sector containing the cell's direction index (CCW convention)
    return candidates[0]

alt_sectors = [[] for _ in range(6)]
for c in g.filled:
    alt_sectors[alt_wedge(c)].append(c)

print('sector sizes:', [len(w) for w in alt_sectors])

# check closure under rot60
ok = True
for j in range(6):
    S = {rot_k(1)(c) for c in alt_sectors[j]}
    if S != set(alt_sectors[(j+1) % 6]):
        print(f"rot: sector {j} -> {sorted(S)[:4]}... != sector {(j+1)%6}")
        ok = False
print('alt sectors closed under rot?', ok)

# closure under refl
ok2 = True
for j in range(6):
    S = {refl_main(c) for c in alt_sectors[j]}
    target = -1
    for k in range(6):
        if S == set(alt_sectors[k]):
            target = k
            break
    print(f"refl: sector {j} -> sector {target}")
    if target < 0:
        ok2 = False
print('alt sectors closed under refl?', ok2)
