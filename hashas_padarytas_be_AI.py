import time
import random
import string
import matplotlib.pyplot as plt
from pathlib import Path

# =================================================
# Hash funkcija
# =================================================
MASK64 = (1 << 64) - 1

def rl(x, r):
    #sukimas i kaire su 64 bitu riba
    r &= 63
    return ((x << r) & MASK64) | (x >> (64 - r))


def hash_string(text):
    a = 0x1A2B3C4D5E6F7788
    b = 0x8899AABBCCDDEEFF
    c = 0x0123456789ABCDEF
    d = 0xF0E1D2C3B4A59687

    # I baitus pavereciam
    data = text.encode("utf-8")

    # Masymas
    for ch in data:
        a ^= ch
        a = rl(a, 7)
        a = (a * 33 + (ch ^ (ch >> 2))) & MASK64

        b ^= rl(ch, 11)
        b = (b * 29 + (ch ^ (ch >> 4))) & MASK64

        c ^= rl(ch, 19)
        c = (c * 35 + (ch ^ (ch >> 6))) & MASK64

        d ^= rl(ch, 23)
        d = (d * 39 + (ch ^ (ch >> 8))) & MASK64

    a ^= rl(b, 13);  a = (a + c) & MASK64
    b ^= rl(c, 17); b = (b + d) & MASK64
    c ^= rl(d, 29); c = (c + a) & MASK64
    d ^= rl(a, 31); d = (d + b) & MASK64

    # bitu -> hex (kad neprintintu dvigubai)
    return f"{a:016x}{b:016x}{c:016x}{d:016x}"

def hash_file(fname):
    try:
        with open(fname, "r", encoding="utf-8") as f:
            content = f.read()
        hash_string(content)
    except FileNotFoundError:
        print("Failas nerastas.")

# =================================================
# Efektyvumo matavimas (konstitucija.txt)
# =================================================
def measure_times(filename, repeats=5):
    with open(filename, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    n = len(all_lines)
    print(f"Failas turi {n} eiluciu.")

    sizes, times = [], []
    step = 1
    while step <= n:
        sizes.append(step)
        elapsed_list = []
        for _ in range(repeats):
            subset = "".join(all_lines[:step])
            start = time.perf_counter()
            _ = hash_string(subset)
            end = time.perf_counter()
            elapsed_list.append(end - start)
        avg = sum(elapsed_list) / repeats
        times.append(avg)
        print(f"Eiluciu: {step}, vidutinis laikas: {avg:.8f} s")
        step *= 2
    return sizes, times

def run_experiment():
    base_dir = Path(__file__).parent
    fname = base_dir / "Files" / "konstitucija.txt"
    if not fname.exists():
        print("Failas konstitucija.txt nerastas salia programos.")
        return
    sizes, times = measure_times(fname, repeats=5)
    plt.figure(figsize=(8,5))
    plt.plot(sizes, times, marker="o")
    plt.xscale("log", base=2)
    plt.xlabel("Eiluciu skaicius (log2)")
    plt.ylabel("Vidutinis hashavimo laikas (s)")
    plt.title("Hashavimo efektyvumas (nuosavas algoritmas)")
    plt.grid(True)
    plt.show()

# =================================================
# Koliziju paieska
# =================================================
def random_string(length: int, rng: random.Random) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(rng.choices(alphabet, k=length))

def collision_test(lengths=None, pairs_per_length: int = 100000, save_file: bool = False):
    """
    Generuoja poras (s1, s2), skaiciuoja hash'us su hash_string
    ir parodo tikras kolizijas (skirtingos poros su tuo paciu hash).
    Pasikartojancias identiskas poras (duplicate inputs) atskiria.
    """
    if lengths is None:
        lengths = [10, 100, 500, 1000]

    rng = random.Random() # Random(42)

    # pasiruosti failui, jei prasyta saugoti
    out_path = Path(__file__).parent / "poros.txt" if save_file else None
    fout = None
    if save_file:
        fout = open(out_path, "w", encoding="utf-8")
        print(f"Rasau poras i: {out_path}")

    seen_hash_to_pair = {} # hash -> pirmoji (s1,s2)
    collisions = 0
    duplicate_inputs = 0
    total_pairs = 0

    for L in lengths:
        if fout:
            fout.write(f"=== Ilgis {L} ===\n")
        for _ in range(pairs_per_length):
            s1 = random_string(L, rng)
            s2 = random_string(L, rng)
            if fout:
                fout.write(f"{s1} {s2}\n")

            h = hash_string(s1 + "|" + s2)
            total_pairs += 1

            prev = seen_hash_to_pair.get(h)
            if prev is None:
                seen_hash_to_pair[h] = (s1, s2)
            else:
                if prev == (s1, s2):
                    duplicate_inputs += 1 # ta pati pora -> ne kolizija
                else:
                    collisions += 1 # tikra kolizija
        if fout:
            fout.write("\n")
    if fout:
        fout.flush()
        fout.close()

    unique_hashes = len(seen_hash_to_pair)
    collision_rate = collisions / total_pairs if total_pairs else 0.0

    print("\n----- Koliziju santrauka -----")
    print(f"Is viso poru:           {total_pairs:,}")
    print(f"Unikaliu hash'u:        {unique_hashes:,}")
    print(f"Pasikartojanciu poru:   {duplicate_inputs:,}  (nera koliziju)")
    print(f"Koliziju:               {collisions:,}")
    print(f"Koliziju daznis:        {collision_rate:.12f}")
    if save_file:
        print(f"Poros issaugotos faile: {out_path}")

# =================================================
# Meniu
# =================================================
def main_menu():
    base = Path(__file__).parent
    while True:
        print("\nPasirinkite veiksma:")
        print("1 - Hash'inti faila")
        print("2 - Hash'inti string")
        print("3 - Paleisti efektyvumo testa su Files/konstitucija.txt")
        print("4 - Koliziju testas (generuoja poras ir skaiciuoja kolizijas)")
        print("q - Baigti")

        opt = input(">>> ").strip().lower()
        if opt == '1':
            fn = input("Iveskite failo kelia (pvz., Files/test.txt): ").strip()
            path = (base / fn) if not Path(fn).is_absolute() else Path(fn)
            hash_file(path)
        elif opt == '2':
            txt = input("Iveskite teksta: ")
            print("Hash:", hash_string(txt))
        elif opt == '3':
            run_experiment()
        elif opt == '4':
            try:
                p = input("Poru per ilgi (default 100000): ").strip()
                pairs = int(p) if p else 100000
            except ValueError:
                pairs = 100000
            save = input("Issaugoti poras i poros.txt? (t/n) [n]: ").strip().lower() == 't'
            lengths = [10, 100, 500, 1000]
            collision_test(lengths=lengths, pairs_per_length=pairs, save_file=save)
        elif opt == 'q':
            break
        else:
            print("Neteisinga ivestis")

if __name__ == "__main__":
    main_menu()