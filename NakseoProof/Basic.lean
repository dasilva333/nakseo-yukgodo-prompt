/-
Lean 4 formal specification of the Nakseo Yukgodo (洛書六觚圖) orbit
classification task.  All code is ASCII-safe (no Unicode symbols).

PREREQUISITES: Lean v4.32.2 toolchain via elan.  Build with `lake build`.
Self-contained (no mathlib; only Lean core).
-/

namespace Nakseo

/-- Structure named Cell with two Int fields q, r. -/
structure Cell where
  q : Int
  r : Int
  deriving Repr, Inhabited

/-- Constructor Cell. -/

def Cell.mk' : Int -> Int -> Cell := Cell.mk

/-- 60-degree rotation about the origin in axial coords: (q, r) |-> (-r, q + r). -/
def rho : Cell -> Cell := fun c => Cell.mk (-c.r) (c.q + c.r)

/-- Reflection about the axis through corner (9, 0). -/
def sig : Cell -> Cell := fun c => Cell.mk (c.q + c.r) (-c.r)

/-- k-fold iterate of rotation. -/
def rhoK : Nat -> Cell -> Cell
  | Nat.zero   => id
  | Nat.succ n => fun c => rho (rhoK n c)

/-- D6 element list. -/
def D6_elems : Nat := 12

/-- Apply the k-th D6 element.  k < 6: rotation k.  k in [6, 12): rotation k-6 then reflection. -/
def applyD6 (k : Nat) (c : Cell) : Cell :=
  if k < 6 then rhoK k c else rhoK (k - 6) (sig c)

/-- UPPER_TEXT_BOUND marker: constants for proofs. -/
theorem rhoK_zero_id : rhoK 0 = id := rfl

theorem D6_elems_eq : D6_elems = 12 := rfl

end Nakseo
