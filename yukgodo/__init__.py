"""Nakseo Yukgodo (洛書六觚圖) reconstruction search framework.

A search program that reverse-engineers the Nakseo Yukgodo (洛書六觚圖)
from Choi Seok-jeong's *Gusuryak* (籌數略) out of the numeric conditions
found in the OCR of its commentary.

Established facts (commentary OCR + cross-check against the 六觚 record of
the *Hanshu* 律曆志):
    - hexagonal lattice with 10 cells per side: center 1 + 9 rings = 271 cells
    - 虛一: the center is left void → 270 cells (共積二百七十)
    - 54 perimeter cells (校計周五十四數); ring k has 6k cells
    - total cells 270 = 6 × (1+2+...+9) = 6 × 45 (通加洛書數六倍)
    - central horizontal row (中觚) has 19 cells (十九爲中觚數也)

Hypotheses (same technique as Choi Seok-jeong's other magic diagrams):
    - place each value 1..270 exactly once
    - the two values at antipodal (point-symmetric) cells form a
      complementary pair summing to 271
"""

__version__ = "0.1.0"
