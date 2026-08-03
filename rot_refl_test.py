import json
from yukgodo.hexgrid import HexGrid
from yukgodo.analysis import rot_k, refl_main
from yukgodo.properties import measure

data = json.load(open('output/orbit_reps_report.json', encoding='utf-8'))
grid = HexGrid()

print('orbit | pen_orig | pen_rot1 | pen_refl')
for rec in data[:3]:
    p, x = rec['canon_p'], rec['canon_x']
    vals = {}
    for t, (a, b) in enumerate(grid.slots):
        L, H = p[t], 271 - p[t]
        vals[a], vals[b] = ((H, L) if x[t] else (L, H))
    pen0 = measure(vals, grid).penalty

    rot_vals = {}
    for c in grid.filled:
        rot_vals[rot_k(1)(c)] = vals[c]
    pen_rot = measure(rot_vals, grid).penalty

    ref_vals = {}
    for c in grid.filled:
        ref_vals[refl_main(c)] = vals[c]
    pen_ref = measure(ref_vals, grid).penalty

    print(f"{rec['orbit']:5d} | {pen0:8.1f} | {pen_rot:8.1f} | {pen_ref:8.1f}")
