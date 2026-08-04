# Verification Report: EXTRA.md & ANALYSIS_F271.md Claims

## Summary Table

| # | Claim | Status | Evidence from 12-orbit data |
|---|-------|--------|------------------------------|
| 1 | Antipodal Wedge Pair Sum Invariant: W_i + W_{i+3} = 12195 | ✅ **Verified** | All 12 orbits (36/36 wedge pairs equal 12195; mean=12195.00) |
| 2 | Antipodal Ray Pair Sum Invariant: R_r + R_{r+3} = 2439 | ✅ **Verified** | All 12 orbits (36/36 ray pairs equal 2439; mean=2439.00) |
| 3 | Opposite Side Pair Sum Invariant: S_j + S_{j+3} = 2710 | ✅ **Verified** | All 12 orbits (36/36 side pairs equal 2710; mean=2710.00) |
| 4 | Corner Antipodal Pair Identity: v(C_k) + v(C_{k+3}) = 271 | ✅ **Verified** | All 12 orbits (36/36 corner pairs equal 271) |
| 5 | **Ring Polynomial Spectrum Invariance** (Σv² per ring) | ❌ **Counterexample** | Ring Σv² has 10 distinct values per ring across the 12 orbits |
| 6 | Parity split: each antipodal pair has one odd + one even | ✅ **Verified** | All 12 orbits show 135/135 pairs satisfy antipodal-parity split |

Because claim 5 breaks down but the others hold, the mathematical
structure is a **strict sublattice of invariants**: the D6 group action and
antipodal pair identities are completely rigid, while high-order energy
functions like Σv² vary across orbits.

...

## Z3 Solver Heuristic Recommendations

### 1. Use Antipodal-Identities First

Leverage the exact identities `W_i+W_{i+3} = 12195`, `R_r+R_{r+3} = 2439`,
`S_j+S_{j+3} = 2710` as global constraints. This eliminates half the
wedge/ray/side variable freedom without losing correctness.  In your model,
this halves the structural constraints you must encode explicitly.

### 2. Exploit Quadratic Residue Balance

Across every antipodal pair `(x, 271-x)`, exactly one value is a quadratic
residue in `F_271` and the other is not (Claims 5, 6). Encoding
`a*x - b*x = 271` with a Legendre-symbol branching rule reduces
search complexity because the Legendre test on the low value tells you the
sign of the residue assignment up-front.

### 3. Warn: Don't Trust Higher-Order Patterns for Pruning

The failure of `Σv²` invariance shows that any heuristic or backtrack pruning
relying on `Σv² = const_k` as a global constraint will exclude valid
solutions. Use `Σv²` bounds only as a local ring-of-interest filter, not as
a hard assertion.

### 4. Solving-Strategy Summary

1. Express everything by slot variables `p_t ∈ {1..135}` (Distinct) and
   flip bits `x_t ∈ {0,1}` using linear ITE encoding via IntVal, not
   binary operators producing non-linear terms.
2. Constrain-side sums directly to 1355 (they're fixed by pairs).
3. Use the antipodal-pair sum identities to reduce variables: e.g. write
   `W_{i+3} := 12195 - W_i` and prove a bound instead of leaving it free.
4. If you prune by `Σv²`, note that ring Σv² is not orbit-invariant, so do
   not assert it as hard constraint.
