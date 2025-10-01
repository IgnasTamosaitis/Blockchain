import time
import matplotlib.pyplot as plt
from pathlib import Path

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

def measure_times(filename, repeats=5):
    with open(filename, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    n = len(all_lines)
    print(f"Failas turi {n} eiluču.")

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

# Meniu
while True:
    print("\nPasirinkite veiksma:")
    print("1 - Hash'inti faila")
    print("2 - Hash'inti string")
    print("3 - Paleisti efektyvumo testa su konstitucija.txt")
    print("q - Baigti")

    opt = input(">>> ").strip().lower()
    if opt == '1':
        fn = input("Iveskite failo pavadinima: ")
        hash_file(fn)
    elif opt == '2':
        txt = input("Iveskite teksta: ")
        print("Hash:", hash_string(txt))
    elif opt == '3':
        run_experiment()
    elif opt == 'q':
        break
    else:
        print("Neteisinga ivestis")