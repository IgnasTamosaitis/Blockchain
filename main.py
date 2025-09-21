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
