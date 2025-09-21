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
        
# ===== Hash funkcija =========================================================

def pulse256(data: bytes) -> str:

    data = pad_message(data)  # Pritaikom padding funkcija duomenims iki 32 baitu bloku

    # Pradiniai skaiciai, pagaminti is konstantos C
    s0 = 0x0123456789ABCDEF
    s1 = (s0 * C + 1) & MASK64
    s2 = (s1 * C + 1) & MASK64
    s3 = (s2 * C + 1) & MASK64

    sum_bytes = sum(data)  # visu baitu suma
    # Pradine busena v (4 skaiciai), sumaisyta su ilgiu ir suma
    v = [
        s1 ^ len(data),                 
        s2 ^ (len(data) << 1),          
        s3 ^ (len(data) << 2),
        (s1 ^ s2 ^ s3) ^ (sum_bytes & 0xFFFFFFFF),
    ]

    # Einam per kiekviena 32 baitu bloka
    for off in range(0, len(data), 32):
        block = data[off:off + 32]                          # vienas blokas
        m = [u64_le(block[i*8:(i+1)*8]) for i in range(4)]  # padalinam i 4 skaicius
        mix_rounds(v, m, 8)                                 # 8 round'ai maisymo

    # Pabaigos papildomas maisymas (12 round'u su padirbtu fake_m)
    for r_idx in range(12):
        fake_m = [
            v[(r_idx + 0) & 3] ^ (C * (r_idx + 1)),
            v[(r_idx + 1) & 3],
            v[(r_idx + 2) & 3],
            v[(r_idx + 3) & 3],
        ]
        mix_rounds(v, fake_m, 1)  # pabaigoje dar karta sumaisom dubenis su fake_m

    # Galutinis sujungimas
    out_words = [v[0] ^ v[2], v[1] ^ v[3], v[0] ^ v[1], v[2] ^ v[3]]
    out = b"".join(to_le8(x) for x in out_words)  # pavercia i baitus
    return out.hex()  # grazina 64 hex simbolius (256 bitu hash)

# ===== Main ==================================================================

def main(argv: List[str]) -> None:
    # Meniu
    print("1) Ivesti teksta ranka")
    print("2) Nuskaityti is failo")
    choice = input("Pasirink (1/2): ")

    if choice == "1":
        s = input("Ivesk teksta: ")
        print("Hash:", pulse256(s.encode()))

    elif choice == "2":
        filename = input("Ivesk failo kelia: ")
        try:
            with open(filename, "rb") as f:
                data = f.read()          # skaitom failo baitus
            print("Hash:", pulse256(data))
        except FileNotFoundError:
            print("Klaida: failas nerastas.")

    else:
        print("Netinkamas pasirinkimas. Paleisk dar karta ir rinkis 1 arba 2.")

if __name__ == "__main__":
    main(sys.argv)