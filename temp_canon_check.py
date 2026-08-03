import json
from yukgodo.hexgrid import HexGrid
from yukgodo.analysis import D6
from yukgodo.z3model import build_model
from z3 import sat
import time

grid = HexGrid()
g6 = D6(grid)

recs = json.load(open('output/orbit_reps_report.json', encoding='utf-8'))
rec = recs[0]
p_correct, x_correct = tuple(rec['canon_p']), tuple(rec['canon_x'])

canon = g6.canonical_px(p_correct, x_correct)
print('Original (canon_p-ref, canon_x-ref) first 8:', canon[0][:8], canon[1][:8])
print('Differs?', (canon[0], canon[1]) != (p_correct, x_correct))

w_mirror = []
for t in range(135):
    w_mirror.append(int(rec['canon_p'][t]))
print('len:', len(w_mirror))

flips, pairs, solver = build_model(grid, timeout_s=120)
print('solver built')

rc = solver.check()
print('rc:', rc)
if rc == sat:
    m = solver.model()
    pw = tuple(m.eval(p).as_long() for p in pairs)
    xw = tuple(1 if bool(m.eval(x, model_completion=True)) else 0 for x in flips)
    canon_full = g6.canonical_px(pw, xw)
    print('Pen 6.0 achieved, canonical form first 8:')
    print('  canon_p first 8:', canon_full[0][:8])
    print('  canon_x first 8:', canon_full[1][:8])
    print('Equal to stored canon?', canon_full == canon)
