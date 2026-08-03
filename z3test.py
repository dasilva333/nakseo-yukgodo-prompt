import time
import z3

T = 135
S = z3.SolverFor("QF_FD")
p = [z3.Int(f"p{i}") for i in range(T)]
b = [z3.Int(f"x{i}") for i in range(T)]
S.add([z3.And(1 <= p[i], p[i] <= T) for i in range(T)])
S.add([z3.And(0 <= b[i], b[i] <= 1) for i in range(T)])
S.add(z3.Distinct(p))
W = 271
# v_A = p_t + b_t*(271 - 2 p_t) = p_t + W*b_t - 2 b_t p_t
# v_B = W - v_A
terms = []
for t in range(T):
    terms.append(p[t] + W*b[t] - 2*b[t]*p[t])
r = z3.Sum(terms)
S.add(r == 1000)

t0 = time.time()
rc = S.check()
print('rc:', rc, 'time:', time.time() - t0)
if rc == z3.sat:
    m = S.model()
    print('first 8 p:', [m[p[i]].as_long() for i in range(8)])
    print('first 8 b:', [m[b[i]].as_long() for i in range(8)])
else:
    print('model unavailable')

