# Deep Analysis of Nakseo Yukgodo (洛書六觚圖): Retaining Only the Valid Structure

Comparing Yukgodo's numerical landscape with modern mathematical structures leaves a strong, but carefully bounded, conclusion. The core is the **negation structure in $\mathbb{F}_{271}$ and the automatically induced quadratic-residue balance**.

There is no identity with a Paley graph, Riemann-zeta zeros, or GUE eigenvalue statistics; those claims are therefore excluded. What remains is this:

> Yukgodo is an integer-permutation optimization problem that realizes the negation structure of $\mathbb{F}_{271}$ on a hexagonal grid. This necessarily produces Paley-like shadows such as quadratic-residue balance. The shared structure is the finite-field structure of antipodal complement pairs; everything else is an analogy at the level of constraint satisfaction.

## 1. Validation Basis

The current diagram is the optimum in `output/solution.json`; its geometric model is the radius-9 hexagonal grid defined in `yukgodo/hexgrid.py`.

| Item | Value | Meaning |
|---|---:|---|
| Total cells | 271 | Hexagonal grid including the center |
| Filled cells | 270 | Center `虛一` excluded |
| Antipodal sum | 271 | Values in opposing cells sum to this value |
| Antipodal pairs | 135 | $270 / 2$ |
| Cells in ring $k$ | $6k$ | Geometric interpretation of `添六` |
| Cells in a wedge | 45 | Odd, so exact halving is impossible |
| Cells in a ray | 9 | Odd, so exact halving is impossible |

The principal objective targets are:

- Ring sum: $3k\times271=813k$
- Axis sum: $9\times271=2439$
- Wedge target: $45\times271/2=6097.5$
- Ray target: $9\times271/2=1219.5$
- Theoretical penalty floor: wedges 3.0 + rays 3.0 = 6.0

## 2. A Valid Identity: Negation in $\mathbb{F}_{271}$

Viewing values as nonzero elements of $\mathbb{F}_{271}$, the antipodal condition is

```text
v(-c) = 271 - v(c) ≡ -v(c) (mod 271)
```

Thus the labeling behaves like an odd function under central symmetry.

Direct checks give:

```text
p mod 4 = 3
Legendre(-1) = -1
antipodal odd labeling = True
```

This is an exact mathematical identity, not a metaphor. Since 271 is prime and $271\equiv3\pmod4$, $-1$ is a quadratic non-residue. Consequently, if $x$ is a quadratic residue then $-x$ is a non-residue, and conversely.

Every antipodal pair $\{x,-x\}$ therefore contains exactly:

```text
one quadratic residue + one quadratic non-residue
```

## 3. Automatically Induced Quadratic-Residue Balance

Each ring and axis is a union of antipodal pairs, so quadratic residues (QR) and non-residues (QNR) occur in exactly equal numbers. This is not evidence of a separate algorithm, but a direct consequence of $x\leftrightarrow-x$.

### Rings

| Ring | Cells | QR | QNR |
|---:|---:|---:|---:|
| 1 | 6 | 3 | 3 |
| 2 | 12 | 6 | 6 |
| 3 | 18 | 9 | 9 |
| 4 | 24 | 12 | 12 |
| 5 | 30 | 15 | 15 |
| 6 | 36 | 18 | 18 |
| 7 | 42 | 21 | 21 |
| 8 | 48 | 24 | 24 |
| 9 | 54 | 27 | 27 |

### Axes

Excluding the center, each axis has 18 cells: nine antipodal pairs.

| Axis | Cells | QR | QNR |
|---:|---:|---:|---:|
| 0 | 18 | 9 | 9 |
| 1 | 18 | 9 | 9 |
| 2 | 18 | 9 | 9 |

### Ring-Walk Differences

The QR/QNR classes of adjacent differences around each ring are also exactly balanced. On the opposite side of a ring, a value difference is negated; because $\operatorname{Legendre}(-d)=-\operatorname{Legendre}(d)$, this too is a shadow of antipodal complement pairing.

| Ring | QR differences | Total | Ratio |
|---:|---:|---:|---:|
| 1 | 3 | 6 | 0.500 |
| 2 | 6 | 12 | 0.500 |
| 3 | 9 | 18 | 0.500 |
| 4 | 12 | 24 | 0.500 |
| 5 | 15 | 30 | 0.500 |
| 6 | 18 | 36 | 0.500 |
| 7 | 21 | 42 | 0.500 |
| 8 | 24 | 48 | 0.500 |
| 9 | 27 | 54 | 0.500 |

## 4. A Valid Arithmetic Lower Bound: $\pm0.5$ for Wedges and Rays

The optimal solution's residual imbalance is:

```text
wedges = [6097, 6098, 6098, 6098, 6097, 6097]
target = 6097.5
deviation = [-0.5, +0.5, +0.5, +0.5, -0.5, -0.5]

rays = [1219, 1220, 1219, 1220, 1219, 1220]
target = 1219.5
deviation = [-0.5, +0.5, -0.5, +0.5, -0.5, +0.5]
```

This is integer arithmetic internal to Yukgodo, not a separate spectral phenomenon.

- A wedge contains 45 cells.
- Opposing wedges correspond through 45 antipodal pairs, so their combined sum is $45\times271=12195$.
- Half is 6097.5, but a wedge sum must be an integer.
- The best possible values are therefore 6097 and 6098.

Similarly, a ray has 9 cells; opposing rays total $9\times271=2439$, whose half is 1219.5. Integer sums cannot reach it, so 1219 and 1220 are optimal.

The final penalty of 6.0 is therefore the arithmetic lower bound imposed by halving odd-sized groups of integers:

```text
wedges: 6 × 0.5 = 3.0
rays:   6 × 0.5 = 3.0
total:            6.0
```

## 5. The Most Accurate Modern Analogy

The best modern analogy is a **constraint-satisfaction problem (CSP)**, a **balanced block design**, and **sparse partial-sum constraints**.

| Constraint | Character |
|---|---|
| Antipodal-pair sum 271 | 135 strong one-to-one constraints |
| Ring sum $813k$ | Automatic from antipodal pairing |
| Axis sum 2439 | Automatic from antipodal pairing |
| Outer-side sum 1355 | Additional boundary balance constraint |
| Wedges 6097/6098 | Optimal halving of 45-cell blocks |
| Rays 1219/1220 | Optimal halving of 9-cell blocks |

Each value participates in multiple checks, so moving one value perturbs distant sum constraints—the behavior of a sparse constraint graph. It is not itself a linear parity check, so the accurate claim is resemblance at the level of sparse constrained optimization, not identity with LDPC codes.

## 6. Final Assessment

| Hypothesis | Assessment | Reason |
|---|---|---|
| Yukgodo antipodal pairs are $x\leftrightarrow-x$ in $\mathbb{F}_{271}$ | True | $v(-c)\equiv-v(c)\pmod{271}$ |
| Every antipodal pair has one QR and one QNR | True | $271\equiv3\pmod4$, $\operatorname{Legendre}(-1)=-1$ |
| QR balance in rings and axes arises automatically | True | Rings and axes are unions of antipodal pairs |
| The wedge/ray $\pm0.5$ is an arithmetic optimum | True | Half-integer targets for odd-sized blocks |
| Yukgodo resembles CSP/sparse constraint optimization | Strong analogy | Overlapping partial-sum and complement-pair constraints |

In short, the striking part of Yukgodo is not that it reproduces a grand external theory. It is that the small arithmetic principle $x\leftrightarrow-x\pmod{271}$ propagates across a 270-cell hexagonal grid, simultaneously producing global balance in rings, axes, wedges, and rays.