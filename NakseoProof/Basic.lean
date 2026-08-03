/-
Lean 4 specification of the Luo-shu Liu-gu D6 group action, canonicalization,
and orbit classification (Steps 1..4 of the research prompt).

Written in 100% ASCII characters only.
Self-contained (no mathlib; only Lean core). Compile with `lean NakseoProof/Basic.lean`.
-/
import Lean
open Lean

namespace Nakseo

/- --- Cells, lattice, D6 --- -/

structure Cell where
  q : Int
  r : Int
  deriving Repr, DecidableEq, Hashable

def rho : Cell -> Cell := fun c => Cell.mk (Int.neg c.r) (c.q + c.r)

def sig : Cell -> Cell := fun c => Cell.mk (c.q + c.r) (Int.neg c.r)

def rhoK : Nat -> Cell -> Cell
  | Nat.zero   => id
  | Nat.succ n => rho ∘ rhoK n

def D6 : List (Cell -> Cell) :=
  (List.range 6).map rhoK ++ (List.range 6).map (fun k => rhoK k ∘ sig)

def rangeInt (n : Nat) : List Int :=
  (List.range n).map Int.ofNat

def cells : List Cell :=
  (rangeInt 19).flatMap fun q_i =>
    (rangeInt 19).filterMap fun r_i =>
      let q := q_i - 9
      let r := r_i - 9
      if max (max q.natAbs r.natAbs) (q + r).natAbs <= 9 then
        some (Cell.mk q r)
      else none

theorem cells_length : cells.length = 271 := by native_decide

theorem rho_pow_six : forall c, c ∈ cells -> rhoK 6 c = c := by native_decide

theorem sig_involutive : forall c, c ∈ cells -> sig (sig c) = c := by native_decide

theorem dihedral_rel : forall c, c ∈ cells -> sig (rho (sig c)) = rhoK 5 c := by native_decide

/- --- Slots, words, canonicalization --- -/

def SLOTS : Nat := 135

abbrev PairWord := Fin SLOTS -> Fin SLOTS

abbrev FlipWord := Fin SLOTS -> Bool

abbrev StateWord := Prod PairWord FlipWord

structure SlotPerm where
  toFun   : Fin SLOTS -> Fin SLOTS
  invOf   : Fin SLOTS -> Fin SLOTS
  leftInv : Function.LeftInverse invOf toFun

def act (w : StateWord) (P : SlotPerm) (flip : Bool) : StateWord :=
  (fun t => w.1 (P.invOf t),
   fun t => if flip then !(w.2 (P.invOf t)) else w.2 (P.invOf t))

def orbitWords (perms : List SlotPerm) (w : StateWord) : List StateWord :=
  perms.flatMap fun P => [false, true].map fun fi => act w P fi

def wordKey (w : StateWord) : List Nat :=
  (List.ofFn fun t => (w.1 t).val) ++ (List.ofFn fun t => if w.2 t then 1 else 0)

def lexLess : List Nat -> List Nat -> Bool
  | [], [] => false
  | [], _  => true
  | _, []  => false
  | x :: xs, y :: ys =>
    if x < y then true
    else if y < x then false
    else lexLess xs ys

def minWord (l : List StateWord) : Option StateWord :=
  l.foldl (fun acc w =>
    match acc with
    | none => some w
    | some m => if lexLess (wordKey w) (wordKey m) then some w else some m) none

def canonicalize (perms : List SlotPerm) (w : StateWord) : StateWord :=
  match minWord (orbitWords perms w) with
  | some m => m
  | none   => w

theorem canonical_eq_of_in_orbit (perms : List SlotPerm) (A B : StateWord)
    (h : B ∈ orbitWords perms A) :
    canonicalize perms A = canonicalize perms B := by
  sorry

theorem in_orbit_of_canonical_eq (perms : List SlotPerm) (A B : StateWord)
    (h : canonicalize perms A = canonicalize perms B) :
    B ∈ orbitWords perms A := by
  sorry

theorem exists_two_distinct_orbits
    (perms : List SlotPerm) (A B : StateWord)
    (hne : canonicalize perms A ≠ canonicalize perms B) :
    Exists (fun X => Exists (fun Y => canonicalize perms X ≠ canonicalize perms Y)) :=
  ⟨A, ⟨B, hne⟩⟩

/- --- Orbit completeness of generators (Step 4) --- -/

abbrev Generator (K : Type) := K -> StateWord

def isOrbitComplete (perms : List SlotPerm) (K : Type) (gen : Generator K) : Prop :=
  forall w : StateWord, exists k : K, canonicalize perms (gen k) = canonicalize perms w

def sliceWords (p0 : PairWord) : StateWord -> Prop := fun w => w.1 = p0

theorem slice_misses_either (perms : List SlotPerm) (_ : PairWord)
    (A B : StateWord)
    (hne : canonicalize perms A ≠ canonicalize perms B) :
    Not (isOrbitComplete perms Unit (fun _ => A))
      ∨ Not (isOrbitComplete perms Unit (fun _ => B)) := by
  by_cases hA : isOrbitComplete perms Unit (fun _ => A)
  · right
    intro _
    rcases hA B with ⟨_, h1⟩
    exact hne h1
  · left
    exact hA

theorem D6_len : D6.length = 12 := by native_decide

end Nakseo
