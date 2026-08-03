# Frontier Model Research Prompt: Complete Orbit Classification & Generator Completeness Proof for Nakseo Yukgodo (洛書六觚圖)

## 1. Executive Context & Objective

We are analyzing the mathematical structure of **Nakseo Yukgodo (洛書六觚圖)** from Choi Seok-jeong's 1700 AD treatise *Gusuryak (九數略)*. 

The puzzle consists of a hexagonal grid of radius $R=9$ containing 271 cells. Excluding the center cell (虚一), 270 values from $1 \dots 270$ are placed on the vertices/cells under strict spatial sum constraints:
1. **Antipodal Complementary Pair**: $v(c) + v(-c) = 271$.
2. **Outer Side Sum**: Sum of 10 cells on each of 6 sides = $1355$.
3. **Wedge Sector Sum**: Sum of 45 cells in each 60° sector $\approx 6097.5$ ($6097 / 6098$).
4. **Ray Corner Sum**: Sum of 9 cells along center-to-corner rays $\approx 1219.5$ ($1219 / 1220$).
5. **Optimal Theoretical Penalty Floor**: $P \ge 6.0$.

### Environment & Toolchain Setup (Already Configured)
- **Lean 4 Toolchain**: Installed and available via `elan` (`Lean v4.32.2` & `Lake v5.0.0`).
- **Isolated Python Virtual Environment**: Created in `./venv/`. All required dependencies (`z3-solver 5.0.0.0`, `scipy`, `numpy`, `matplotlib`) are installed.
- **Verification Execution**: All Lean 4 code blocks can be compiled/checked using `lake` or `lean`, and Python scripts should be run with `source ./venv/bin/activate`.

---

## 2. Mathematical Formalization & Scope

### Spatial Symmetry Group $D_6$
The spatial symmetry group of the regular 2D hexagonal grid is the **Dihedral group $D_6$** of order 12 (comprising 6 rotational symmetries and 6 reflectional symmetries). Note that antipodal inversion $c \mapsto -c$ corresponds to a 180° rotation ($R_{180^\circ} \in D_6$). Thus, all symmetry operations are defined strictly under $D_6$.

### Orbit Completeness Definition & Scope
Let $\mathcal{S}^* = \{g \in \text{Grid} \mid \text{Penalty}(g) = 6.0\}$ be the set of optimal solutions. 
The group $D_6$ acts on $\mathcal{S}^*$. The solution space partitions into equivalence classes (orbits) $\mathcal{S}^* / D_6$.
A deterministic generator function $f : \mathcal{K} \to \mathcal{S}^*$ is defined as **orbit-complete** if its image $f(\mathcal{K})$ intersects **every** orbit in $\mathcal{S}^* / D_6$.

---

## 3. The 4-Step Task

We request a formal mathematical analysis, compiled Lean 4 type-level specification, and runnable Python/Z3 verification script for the following 4 milestones:

### Step 1: $D_6$ Group Action Formalization
Formally define the 12 group elements of $D_6$ acting on the 135 antipodal slot pairs of the radius-9 hexagonal grid.

### Step 2: Canonicalization under $D_6$
Define a canonicalization mapping $\mathrm{Can}: \mathcal{S}^* \to \mathcal{S}^*$ such that two solutions $A, B \in \mathcal{S}^*$ belong to the same $D_6$-orbit if and only if $\mathrm{Can}(A) = \mathrm{Can}(B)$.

### Step 3: Explicit Distinct Orbit Identification
Construct or prove the existence of explicit optimal solutions $A, B \in \mathcal{S}^*$ such that $\mathrm{Can}(A) \ne \mathrm{Can}(B)$ (demonstrating the existence of multiple non-isomorphic $D_6$-orbits in the optimal solution space).

### Step 4: Generator Expressiveness & Completeness Test
Evaluate whether the existing Pruning Backtracking DFS generator (which searches a $2^{135}$ orientation slice) intersects all orbits in $\mathcal{S}^* / D_6$, prove its orbit-incompleteness against enumerated solutions, and specify the minimal parameterization (e.g. orbit-representative seeding) required to achieve orbit-completeness in principle.

---

## 4. Reference Files Included in Workspace Context

1. `GENERATOR.md`: Complete mathematical formulation, side/wedge/ray targets, penalty floor proofs, and experimental hypothesis test logs.
2. `z3_solver_spec.py`: Python code specifying the constraint system, antipodal pairing, penalty metrics, and deterministic search pruning logic.

---

## 5. Required Output Structure

Please structure your response into the following 3 sections:

### Section 1: Group Action & Canonicalization Proof
Provide the explicit mathematical formulation of the $D_6$ action on the 135 slot pairs and the canonicalization function $\mathrm{Can}(g)$.

### Section 2: Compiled Lean 4 Specification
Provide a complete, compilable Lean 4 file specifying `D6`, `NakseoGrid`, `D6_Action`, and the orbit completeness theorems.

### Section 3: Z3 / Python Verification Script
Provide a Python script (executable within `./venv/`) using `z3-solver` and `numpy` that implements the $D_6$ canonicalizer and tests for distinct orbit representatives.
