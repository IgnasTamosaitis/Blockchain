import time
import matplotlib.python as plt
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

    # bitu -> hex
    r1 = f"{a:016x}"
    r2 = f"{b:016x}"
    r3 = f"{c:016x}"
    r4 = f"{d:016x}"
    print("Hash:", r1 + r2 + r3 + r4)


def hash_file(fname):
    try:
        with open(fname, "r", encoding="utf-8") as f:
            content = f.read()
        hash_string(content)
    except FileNotFoundError:
        print("Failas nerastas.")


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