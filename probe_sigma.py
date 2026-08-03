from yukgodo.hexgrid import HexGrid
from yukgodo.analysis import refl_main, rot60

g = HexGrid()
sigma = refl_main

print("corners:", g.corners())
print("sigma(corners):", [sigma(c) for c in g.corners()])

wedge0 = g.wedges[0]
print()
print("wedge 0 len:", len(wedge0))
print("corner (9,0) in wedge 0?", (9,0) in wedge0)
print("wedge_of[(9,0)] =", g.wedge_of[(9,0)])

# The D6 *spatial* group requires wedges and rays to be permuted by the action.
print()
print("sigma(wedge_j) partition equality:")
for j, w in enumerate(g.wedges):
    S = {sigma(c) for c in w}
    match = [k for k, w2 in enumerate(g.wedges) if set(w2) == S]
    print(f"  sigma(wedge {j}) == wedges {match}")

print()
print("sigma(ray_j):")
for j, w in enumerate(g.rays):
    S = {sigma(c) for c in w}
    match = [k for k, w2 in enumerate(g.rays) if set(w2) == S]
    print(f"  sigma(ray {j}) == rays {match}")

print()
print("sigma(side_j):")
for j, w in enumerate(g.sides):
    S = {sigma(c) for c in w}
    match = [k for k, w2 in enumerate(g.sides) if set(w2) == S]
    print(f"  sigma(side {j}) == sides {match}")
