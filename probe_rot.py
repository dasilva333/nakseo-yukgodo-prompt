from yukgodo.hexgrid import HexGrid
from yukgodo.analysis import rot60, refl_main

g = HexGrid()
print("Does rot60 permute the wedges as sets?")
ok = True
for j, w in enumerate(g.wedges):
    S = {rot60(c) for c in w}
    match = [k for k, w2 in enumerate(g.wedges) if set(w2) == S]
    print(f"  rot(wedge {j}) == wedge {match}")
    if not match:
        ok = False
print("OK:", ok)

print()
print("Does refl_main permute the rays as sets?")
ok2 = True
for j, w in enumerate(g.rays):
    S = {refl_main(c) for c in w}
    match = [k for k, w2 in enumerate(g.rays) if set(w2) == S]
    if not match:
        ok2 = False
        print(f"  refl(ray {j}) == rays {match}")
print("OK (for rays):", ok2)
