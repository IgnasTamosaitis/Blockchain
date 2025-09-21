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

