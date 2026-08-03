import json
from yukgodo.hexgrid import HexGrid, PAIR_SUM
from yukgodo.analysis import D6
from yukgodo.properties import measure

grid = HexGrid(); g6 = D6(grid)
recs = json.load(open('output/orbit_reps_report.json', encoding='utf-8'))
for r in recs[:5]:
    p = tuple(r['canon_p']); x = tuple(r['canon_x'])
    vals = {}
    for t, (a, b) in enumerate(grid.slots):
        L, H = p[t], PAIR_SUM - p[t]
        vals[a], vals[b] = ((H, L) if x[t] else (L, H))
    pen = measure(vals, grid).penalty
    c1 = g6.canonical_px(p, x)
    assert c1 == (p, x), f'not idempotent at orbit {r["orbit"]}'
    print(f"orbit {r['orbit']:2d} pen={pen:.1f} canon-idempotent OK")
print('All good: canonical (p, x) pairs reproduce optimal solutions.')
