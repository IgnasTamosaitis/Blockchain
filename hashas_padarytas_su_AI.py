import sys
import time
import random
import string
import secrets
from pathlib import Path
from typing import List

# --- Matplotlib (grafikams). Jei neįdiegta, parodysime žinutę ir praleisime grafikus.
try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False

# =========================
#  AI sugeneruotas hash: pulse256
# =========================

MASK64 = (1 << 64) - 1

def rotl(x: int, r: int) -> int:
    return ((x << r) | (x >> (64 - r))) & MASK64

def rotr(x: int, r: int) -> int:
    return ((x >> r) | (x << (64 - r))) & MASK64

def u64_le(b: bytes) -> int:
    return int.from_bytes(b, "little")

def to_le8(x: int) -> bytes:
    return x.to_bytes(8, "little")

# Konstantos
C = 0x9E3779B97F4A7C15
MC = [
    0xBF58476D1CE4E5B9,
    0x94D049BB133111EB,
    0xC2B2AE3D27D4EB4F,
    0x85EBCA77C2B2AE63,
]
R = [13, 17, 43, 29]

def pad_message(msg: bytes) -> bytes:
    bitlen = len(msg) * 8
    out = bytearray(msg)
    out.append(0x80)
    while (len(out) + 8) % 32 != 0:
        out.append(0x00)
    out += bitlen.to_bytes(8, "little")
    return bytes(out)

def mix_rounds(v: List[int], m: List[int], rounds: int) -> None:
    for r_idx in range(rounds):
        for i in range(4):
            add = (m[(i + r_idx) & 3] + MC[i] * (r_idx + 1)) & MASK64
            v[i] = (v[i] + add) & MASK64
            v[(i + 3) & 3] ^= rotr(v[i], R[i])
            v[i] = (v[i] * (MC[(i + 1) & 3] | 1)) & MASK64

        a = rotl(v[0], 32) ^ v[2]
        b = rotl(v[1], 24) ^ v[3]
        c = rotr(v[2], 17) ^ v[0]
        d = rotr(v[3], 13) ^ v[1]
        v[0], v[1], v[2], v[3] = a, b, c, d

def pulse256(data: bytes) -> str:
    data = pad_message(data)

    s0 = 0x0123456789ABCDEF
    s1 = (s0 * C + 1) & MASK64
    s2 = (s1 * C + 1) & MASK64
    s3 = (s2 * C + 1) & MASK64

    sum_bytes = sum(data)
    v = [
        s1 ^ len(data),
        s2 ^ (len(data) << 1),
        s3 ^ (len(data) << 2),
        (s1 ^ s2 ^ s3) ^ (sum_bytes & 0xFFFFFFFF),
    ]

    for off in range(0, len(data), 32):
        block = data[off:off + 32]
        m = [u64_le(block[i*8:(i+1)*8]) for i in range(4)]
        mix_rounds(v, m, 8)

    for r_idx in range(12):
        fake_m = [
            v[(r_idx + 0) & 3] ^ (C * (r_idx + 1)),
            v[(r_idx + 1) & 3],
            v[(r_idx + 2) & 3],
            v[(r_idx + 3) & 3],
        ]
        mix_rounds(v, fake_m, 1)

    out_words = [v[0] ^ v[2], v[1] ^ v[3], v[0] ^ v[1], v[2] ^ v[3]]
    out = b"".join(to_le8(x) for x in out_words)
    return out.hex()

# Patogios “wrapper” funkcijos, kad elgtųsi kaip tavo asmeninis hash
def hash_text(text: str) -> str:
    return pulse256(text.encode("utf-8"))

def hash_pair(s1: str, s2: str) -> str:
    # aiškus skyriklis, kad (ab,c) != (a,bc)
    return hash_text(f"{s1}|{s2}")

def hash_file_path(path: Path) -> None:
    try:
        with open(path, "rb") as f:
            data = f.read()
        print("Hash:", pulse256(data))
    except FileNotFoundError:
        print("Failas nerastas.")

# ======================
#  Efektyvumo testas (1,2,4,8... eilutės)
# ======================
def measure_times(filename: Path, repeats: int = 5):
    with open(filename, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    n = len(all_lines)
    print(f"Failas turi {n} eiluciu.")
    sizes, times = [], []
    step = 1
    while step <= n:
        sizes.append(step)
        elapsed = []
        for _ in range(repeats):
            subset = "".join(all_lines[:step])
            t0 = time.perf_counter()
            _ = hash_text(subset)
            t1 = time.perf_counter()
            elapsed.append(t1 - t0)
        avg = sum(elapsed) / repeats
        times.append(avg)
        print(f"Eilutes: {step:>8}, vidutinis laikas: {avg:.8f} s")
        step *= 2
    return sizes, times

def run_experiment():
    if not HAS_MPL:
        print("Matplotlib neinstaliuotas. Paleisk: pip install matplotlib")
        return
    base = Path(__file__).parent
    fname = base / "Files" / "konstitucija.txt"
    if not fname.exists():
        print("Failas Files/konstitucija.txt nerastas.")
        return
    sizes, times = measure_times(fname, repeats=5)
    plt.figure(figsize=(8,5))
    plt.plot(sizes, times, marker="o")
    plt.xscale("log", base=2)
    plt.xlabel("Eiluciu skaicius (log2)")
    plt.ylabel("Vidutinis hashavimo laikas (s)")
    plt.title("Hashavimo efektyvumas (pulse256)")
    plt.grid(True)
    plt.show()

# ======================
#  Koliziju testas (atskiria dublikatus)
# ======================
def random_string_n(n: int, rng: random.Random) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(rng.choices(alphabet, k=n))

def collision_test(lengths=None, pairs_per_length: int = 100000, save_file: bool = False):
    if lengths is None:
        lengths = [10, 100, 500, 1000]

    rng = random.Random()
    out_path = Path(__file__).parent / "poros.txt"
    fout = open(out_path, "w", encoding="utf-8") if save_file else None
    if fout:
        print(f"Rasau poras i: {out_path}")

    seen_hash_to_pair = {}
    collisions = 0
    duplicate_inputs = 0
    total_pairs = 0

    for L in lengths:
        if fout:
            fout.write(f"=== Ilgis {L} ===\n")
        for _ in range(pairs_per_length):
            s1 = random_string_n(L, rng)
            s2 = random_string_n(L, rng)
            if fout:
                fout.write(f"{s1} {s2}\n")

            h = hash_pair(s1, s2)
            total_pairs += 1

            prev = seen_hash_to_pair.get(h)
            if prev is None:
                seen_hash_to_pair[h] = (s1, s2)
            else:
                if prev == (s1, s2):
                    duplicate_inputs += 1
                else:
                    collisions += 1
        if fout:
            fout.write("\n")

    if fout:
        fout.close()

    unique_hashes = len(seen_hash_to_pair)
    collision_rate = (collisions / total_pairs) if total_pairs else 0.0

    print("\n----- Koliziju santrauka -----")
    print(f"Is viso poru:           {total_pairs:,}")
    print(f"Unikaliu hash'u:        {unique_hashes:,}")
    print(f"Pasikartojanciu poru:   {duplicate_inputs:,}  (ne kolizijos)")
    print(f"Koliziju:               {collisions:,}")
    print(f"Koliziju dagnis:        {collision_rate:.12f}")
    if save_file:
        print(f"Poros issaugotos faile: {out_path}")

# ======================
#  Lavinos efektas (1 simbolio mutacija)
# ======================
def _mutate_one_char(s: str, rng: random.Random) -> str:
    if not s:
        return "a"
    idx = rng.randrange(len(s))
    alphabet = string.ascii_letters + string.digits
    old = s[idx]
    new = rng.choice(alphabet)
    while new == old:
        new = rng.choice(alphabet)
    return s[:idx] + new + s[idx+1:]

def _bits_diff_from_hex(h1: str, h2: str) -> int:
    x = int(h1, 16) ^ int(h2, 16)
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")

def _hex_diff(h1: str, h2: str) -> int:
    return sum(a != b for a, b in zip(h1, h2))

def avalanche_test(samples=100_000, str_len=64, seed=None):
    rng = random.Random(seed)

    bits_min = 256
    bits_max = 0
    bits_sum = 0

    hex_min = 64
    hex_max = 0
    hex_sum = 0

    for _ in range(samples):
        s1 = random_string_n(str_len, rng)
        s2 = random_string_n(str_len, rng)
        h1 = hash_pair(s1, s2)

        if rng.random() < 0.5:
            s1m, s2m = _mutate_one_char(s1, rng), s2
        else:
            s1m, s2m = s1, _mutate_one_char(s2, rng)

        h2 = hash_pair(s1m, s2m)

        bd = _bits_diff_from_hex(h1, h2)
        hd = _hex_diff(h1, h2)

        bits_sum += bd
        hex_sum += hd
        if bd < bits_min: bits_min = bd
        if bd > bits_max: bits_max = bd
        if hd < hex_min:  hex_min = hd
        if hd > hex_max:  hex_max = hd

    bits_avg = bits_sum / samples
    hex_avg = hex_sum / samples

    print("\n----- Lavinos efekto rezultatai -----")
    print(f"Bandymu kiekis: {samples:,} | eilutes ilgis: {str_len}")
    print("Bitu lygmuo (is 256 bitu):")
    print(f"  min: {bits_min:3d} bit ({bits_min/256*100:6.2f}%)")
    print(f"  max: {bits_max:3d} bit ({bits_max/256*100:6.2f}%)")
    print(f"  avg: {bits_avg:6.2f} bit ({bits_avg/256*100:6.2f}%)")
    print("Hex lygmuo (is 64 poziciju):")
    print(f"  min: {hex_min:2d} hex ({hex_min/64*100:6.2f}%)")
    print(f"  max: {hex_max:2d} hex ({hex_max/64*100:6.2f}%)")
    print(f"  avg: {hex_avg:6.2f} hex ({hex_avg/64*100:6.2f}%)")

# ======================
#  Negriztamumas / Hiding / Puzzle-friendliness
# ======================
def gen_salt(n_bytes: int = 16) -> str:
    return secrets.token_hex(n_bytes)

def salted_hash(text: str, salt_hex: str) -> str:
    # aiškus skyriklis tarp teksto ir sal'o
    return hash_text(f"{text}|{salt_hex}")

def commitment_create():
    msg = input("Iveskite slaptas zinute (input): ").strip()
    nbytes_in = input("Kiek baitu salt? [16]: ").strip()
    try:
        nbytes = int(nbytes_in) if nbytes_in else 16
    except ValueError:
        nbytes = 16

    salt = gen_salt(nbytes)
    Cmt = salted_hash(msg, salt)

    print("\n--- Commitment (hiding) ---")
    print("Salt (hex):", salt)
    print("Hash (C):  ", Cmt)

    save = input("Issaugoti i commitment.txt? (y/N): ").strip().lower() == "y"
    if save:
        outp = Path(__file__).parent / "commitment.txt"
        with open(outp, "w", encoding="utf-8") as f:
            f.write(f"message (DEMO, realiai NEsaugoti cia): {msg}\n")
            f.write(f"salt_hex: {salt}\n")
            f.write(f"commitment: {Cmt}\n")
        print("Issaugota:", outp)

    salt2 = gen_salt(nbytes)
    C2 = salted_hash(msg, salt2)
    print("\nTas pats input, kitas salt -> kitas hash:")
    print("salt2:", salt2)
    print("C2:   ", C2)

def commitment_verify():
    msg = input("Iveskite zinute (input): ").strip()
    salt_hex = input("Iveskite salt (hex): ").strip()
    C = input("Iveskite commitment hash: ").strip()

    C_chk = salted_hash(msg, salt_hex)
    if C_chk == C:
        print("OK ✓ Commitment teisingas.")
    else:
        print("NE ✗ Commitment neatitinka (neteisingas input arba salt).")

def puzzle_demo():
    rng = random.Random(42)
    pin_digits_in = input("PIN skaitmenu kiekis? [4]: ").strip()
    try:
        PIN_DIG = int(pin_digits_in) if pin_digits_in else 4
    except ValueError:
        PIN_DIG = 4

    pin = "".join(str(rng.randrange(10)) for _ in range(PIN_DIG))
    print(f"\n(Privati info DEMO) Tikslinis PIN: {pin}")

    target = hash_text(pin)
    t0 = time.perf_counter()
    found = None
    for i in range(10**PIN_DIG):
        cand = f"{i:0{PIN_DIG}d}"
        if hash_text(cand) == target:
            found = cand
            break
    t1 = time.perf_counter() - t0
    print(f"Be salt bruteforce rado PIN={found} per {t1:.4f} s, bandymu: {i+1:,}")

    salt = gen_salt(16)
    target2 = salted_hash(pin, salt)
    space = (10**PIN_DIG) * (1 << (8*16))
    print("\nSu salt, jei salt NEZINOMAS:")
    print(f"- Paieskos erdve ~ {space:.2e} kombinaciju. Praktiskai neimanoma bruteforce.")
    t0 = time.perf_counter()
    found2 = None
    for i in range(10**PIN_DIG):
        cand = f"{i:0{PIN_DIG}d}"
        if salted_hash(cand, salt) == target2:
            found2 = cand
            break
    t2 = time.perf_counter() - t0
    print(f"Su ZINOMU salt bruteforce rado PIN={found2} per {t2:.4f} s, bandymu: {i+1:,}")

def hiding_menu():
    print("\n--- Negriztamumo / Hiding / Puzzle demonstracija ---")
    print("a) Sukurti commitment (HASH(input + salt))")
    print("b) Patikrinti commitment")
    print("c) Puzzle demo: bruteforce su / be salt")
    sub = input("Pasirinkite [a/b/c]: ").strip().lower()
    if sub == "a":
        commitment_create()
    elif sub == "b":
        commitment_verify()
    elif sub == "c":
        puzzle_demo()
    else:
        print("Neteisinga pasirinktis.")

# ======================
#  Meniu
# ======================
def main_menu():
    base = Path(__file__).parent
    while True:
        print("\nPasirinkite veiksma:")
        print("1 - Hash'inti faila")
        print("2 - Hash'inti string")
        print("3 - Efektyvumo testas su Files/konstitucija.txt (grafikas)")
        print("4 - Koliziju testas (poru generavimas)")
        print("5 - Lavinos efekto testas (100k poru, skiriasi 1 simboliu)")
        print("6 - Negriztamumo (hiding/puzzle) demonstracija – HASH(input + salt)")
        print("q - Baigti")

        opt = input(">>> ").strip().lower()
        if opt == '1':
            fn = input("Iveskite failo kelia (pvz., Files/test.txt): ").strip()
            path = (base / fn) if not Path(fn).is_absolute() else Path(fn)
            hash_file_path(path)
        elif opt == '2':
            txt = input("Iveskite teksta: ")
            print("Hash:", hash_text(txt))
        elif opt == '3':
            run_experiment()
        elif opt == '4':
            try:
                p = input("Poru per ilgi (default 100000): ").strip()
                pairs = int(p) if p else 100000
            except ValueError:
                pairs = 100000
            save = input("Issaugoti poras i poros.txt? (y/n) [n]: ").strip().lower() == 'y'
            lengths = [10, 100, 500, 1000]
            collision_test(lengths=lengths, pairs_per_length=pairs, save_file=save)
        elif opt == '5':
            try:
                s = input("Kiek bandymu? [100000]: ").strip()
                samples = int(s) if s else 100_000
            except ValueError:
                samples = 100_000
            try:
                l = input("Vienos eilutes ilgis? [64]: ").strip()
                str_len = int(l) if l else 64
            except ValueError:
                str_len = 64
            avalanche_test(samples=samples, str_len=str_len, seed=None)
        elif opt == '6':
            hiding_menu()
        elif opt == 'q':
            break
        else:
            print("Neteisinga ivestis")

if __name__ == "__main__":
    main_menu()