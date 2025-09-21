import sys
from typing import List

# MASK64: kad skaiciai liktu 64 bitu ribose
MASK64 = (1 << 64) - 1

def rotl(x: int, r: int) -> int:
    """Pasukimas i kaire per r bitus (64 bitu ribose)"""
    return ((x << r) | (x >> (64 - r))) & MASK64

def rotr(x: int, r: int) -> int:
    """Pasukimas i desine per r bitus (64 bitu ribose)"""
    return ((x >> r) | (x << (64 - r))) & MASK64

def u64_le(b: bytes) -> int:
    """Is 8 baitu suformuoja, kad maziausias baitas eina pirmas"""
    return int.from_bytes(b, "little")  # perskaito duomenis kaip 64 bitu skaiciu

def to_le8(x: int) -> bytes:
    """Padaro 8 baitus"""
    return x.to_bytes(8, "little")  # pavercia i 8 baitus spausdinimui

# ===== Konstantos maisymui =============================================================
C = 0x9E3779B97F4A7C15  # golden ratio
MC = [                  # 4 skirtingos maisymo konstantos
    0xBF58476D1CE4E5B9,
    0x94D049BB133111EB,
    0xC2B2AE3D27D4EB4F,
    0x85EBCA77C2B2AE63,
]
R = [13, 17, 43, 29]    # kiek pasukti kiekviena zodi (v[0..3])

# ===== Padding ==============================================================

def pad_message(msg: bytes) -> bytes:
  
    bitlen = len(msg) * 8           # pradinio teksto ilgis bitais
    out = bytearray(msg)            # kopija
    out.append(0x80)                # pazymejimas: 1 bitas ir paskui nuliai

    # Paliekam vietos 8 baitams galo ilgiui
    while (len(out) + 8) % 32 != 0:
        out.append(0x00)            # pildom nuliais iki 32*n - 8

    out += bitlen.to_bytes(8, "little")  # gale irasom ilgi
    return bytes(out)

# ===== Mixinimas ===========================================================

def mix_rounds(v: List[int], m: List[int], rounds: int) -> None:
    # v = 4 (state), m = 4 (bloko duomenys)

    for r_idx in range(rounds):          # kartojam round'us (kiek kartu maisom)
        for i in range(4):               # tvarkom kiekviena is 4 v 
            # paimam m elementa (paslinkta pagal round'a) + pridedam konstanta (MC)
            add = (m[(i + r_idx) & 3] + MC[i] * (r_idx + 1)) & MASK64

            v[i] = (v[i] + add) & MASK64

            # i kaimyna (kairini) supilam pasukta v[i] per R[i] bitu (XOR)
            v[(i + 3) & 3] ^= rotr(v[i], R[i])

            # padauginam is nelyginio (MC kitas)
            v[i] = (v[i] * (MC[(i + 1) & 3] | 1)) & MASK64

        # didelis sukimasis: sujungiame poras, kad viskas issimaisytu per v[0..3]
        a = rotl(v[0], 32) ^ v[2]
        b = rotl(v[1], 24) ^ v[3]
        c = rotr(v[2], 17) ^ v[0]
        d = rotr(v[3], 13) ^ v[1]
        v[0], v[1], v[2], v[3] = a, b, c, d
