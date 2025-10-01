import time
import random
import string
import matplotlib.pyplot as plt
from pathlib import Path
import secrets

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
# Lavinos efekto testas
# =================================================
def _rand_str(n, rng):
    alphabet = string.ascii_letters + string.digits
    return ''.join(rng.choices(alphabet, k=n))

def _mutate_one_char(s, rng):
    """Grazina s, kur vienas simbolis pakeistas kitu (visada kitu)."""
    if not s:
        return "a"  # krastinis atvejis
    idx = rng.randrange(len(s))
    alphabet = string.ascii_letters + string.digits
    old = s[idx]
    # parenkam simboli, kuris != old
    new = rng.choice(alphabet)
    while new == old:
        new = rng.choice(alphabet)
    return s[:idx] + new + s[idx+1:]

def _bits_diff_from_hex(h1, h2):
    """Hamingo atstumas bitų lygmenyje tarp dviejų 64-hex (256 bitų) hash’ų."""
    x = int(h1, 16) ^ int(h2, 16)
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")

def _hex_diff(h1, h2):
    """Kiek hex pozicijų skiriasi (0..64)."""
    return sum(a != b for a, b in zip(h1, h2))

def avalanche_test(samples=100_000, str_len=64, seed=None):
    """
    Sugeneruoja 'samples' porų (s1,s2). Kiekvienai porai sukuria
    antrą porą, kuri skiriasi TIK vienu simboliu (s1 ARBA s2).
    Matuoja skirtumą tarp hash’ų bitų ir hex lygmenyse.
    Spausdina min/max/avg (ir procentais).
    """
    rng = random.Random(seed)

    bits_min = 256
    bits_max = 0
    bits_sum = 0

    hex_min = 64
    hex_max = 0
    hex_sum = 0

    for _ in range(samples):
        # bazinė pora
        s1 = _rand_str(str_len, rng)
        s2 = _rand_str(str_len, rng)

        # poros hash
        h1 = hash_string(s1 + "|" + s2)

        # mutacija: pakeiciam VIENA simboli s1 arba s2
        if rng.random() < 0.5:
            s1m = _mutate_one_char(s1, rng)
            s2m = s2
        else:
            s1m = s1
            s2m = _mutate_one_char(s2, rng)

        h2 = hash_string(s1m + "|" + s2m)

        # skirtumai
        bd = _bits_diff_from_hex(h1, h2)   # 0..256
        hd = _hex_diff(h1, h2)             # 0..64

        bits_sum += bd
        hex_sum  += hd

        if bd < bits_min: bits_min = bd
        if bd > bits_max: bits_max = bd
        if hd < hex_min:  hex_min  = hd
        if hd > hex_max:  hex_max  = hd

    # vidurkiai
    bits_avg = bits_sum / samples
    hex_avg  = hex_sum  / samples

    # procentai
    bits_min_pct = bits_min / 256 * 100
    bits_max_pct = bits_max / 256 * 100
    bits_avg_pct = bits_avg / 256 * 100

    hex_min_pct  = hex_min  / 64 * 100
    hex_max_pct  = hex_max  / 64 * 100
    hex_avg_pct  = hex_avg  / 64 * 100

    print("\n----- Lavinos efekto rezultatai -----")
    print(f"Bandymu kiekis: {samples:,} | eilutes ilgis: {str_len}")
    print("Bitu lygmuo (is 256 bitu):")
    print(f"  min: {bits_min:3d} bit ({bits_min_pct:6.2f}%)")
    print(f"  max: {bits_max:3d} bit ({bits_max_pct:6.2f}%)")
    print(f"  avg: {bits_avg:6.2f} bit ({bits_avg_pct:6.2f}%)")
    print("Hex lygmuo (is 64 hex simboliu):")
    print(f"  min: {hex_min:2d} hex ({hex_min_pct:6.2f}%)")
    print(f"  max: {hex_max:2d} hex ({hex_max_pct:6.2f}%)")
    print(f"  avg: {hex_avg:6.2f} hex ({hex_avg_pct:6.2f}%)")

# =================================================
# Negriztamumas
# =================================================
def gen_salt(n_bytes: int = 16) -> str:
    """Grazina atsitiktini salt kaip hex (pvz., 16 baitų = 128 bitų)."""
    return secrets.token_hex(n_bytes)

def salted_hash(text: str, salt_hex: str) -> str:
    return hash_string(f"{text}|{salt_hex}")

def commitment_create():
    """
    Sukuria isipareigojima (commitment):
      salt := atsitiktinis
      C := HASH(input + salt)
    """
    msg = input("Iveskite slapta zinute (input): ").strip()
    nbytes_in = input("Kiek baitu salt? [16]: ").strip()
    try:
        nbytes = int(nbytes_in) if nbytes_in else 16
    except ValueError:
        nbytes = 16

    salt = gen_salt(nbytes)
    C = salted_hash(msg, salt)

    print("\n--- Commitment (hiding) ---")
    print("Salt (hex):", salt)
    print("Hash (C):  ", C)

    save = input("Išsaugoti į commitment.txt? (y/N): ").strip().lower() == "y"
    if save:
        outp = Path(__file__).parent / "commitment.txt"
        with open(outp, "w", encoding="utf-8") as f:
            f.write(f"message (NEsaugoti čia realybėje): {msg}\n")
            f.write(f"salt_hex: {salt}\n")
            f.write(f"commitment: {C}\n")
        print("Išsaugota:", outp)

    # Parodymas, kad tas pats input su skirtingais salt duoda skirtingus hash
    salt2 = gen_salt(nbytes)
    C2 = salted_hash(msg, salt2)
    print("\nTas pats input, kitas salt → kitas hash:")
    print("salt2:", salt2)
    print("C2:   ", C2)

def commitment_verify():
    """
    Patikrina įsipareigojimą:
      duota (input, salt_hex, commitment) – ar HASH(input+salt) sutampa?
    """
    msg = input("Įveskite žinutę (input): ").strip()
    salt_hex = input("Įveskite salt (hex): ").strip()
    C = input("Įveskite commitment hash: ").strip()

    C_chk = salted_hash(msg, salt_hex)
    if C_chk == C:
        print("OK ✓  Commitment teisingas.")
    else:
        print("NE ✓  Commitment neatitinka (neteisingas input arba salt).")

def puzzle_demo():
    """
    Puzzle-friendliness demonstracija su maza paieskos erdve (PIN):
    - Be salt 4 skaitmenu PIN galima subruteforcinti labai greitai.
    - Su salt, jeigu salt nezinomas, paieskos erdve tampa milziniska.
    - Jei salt zinomas, bruteforce islieka imanomas mazoms erdvems.
    """
    import random
    rng = random.Random(42)

    # Pasirenkam atsitiktini 4-skaitmeni PIN
    pin_digits_in = input("PIN skaitmenų kiekis? [4]: ").strip()
    try:
        PIN_DIG = int(pin_digits_in) if pin_digits_in else 4
    except ValueError:
        PIN_DIG = 4

    pin = "".join(str(rng.randrange(10)) for _ in range(PIN_DIG))
    print(f"\n(Privati reiksme demonstracijai) Tikslinis PIN: {pin}")

    # 1) Be salt – bruteforce
    target = hash_string(pin)
    start = time.perf_counter()
    found = None
    for i in range(10**PIN_DIG):
        cand = f"{i:0{PIN_DIG}d}"
        if hash_string(cand) == target:
            found = cand
            break
    t1 = time.perf_counter() - start
    print(f"Be salt bruteforce rado PIN={found} per {t1:.4f} s, bandymu: {i+1:,}")

    # 2) Su salt, bet salt nezinomas – paieskos erdve milziniska
    salt = gen_salt(16)  # 128-bit salt
    target2 = salted_hash(pin, salt)
    space = (10**PIN_DIG) * (1 << (8*16))  # PIN erdve * 2^(8*salt_bytes)
    print("\nSu salt, jei salt NEZINOMAS (tik zinomas hash):")
    print(f"- Paieskos erdve ≈ {space:.2e} kombinacijų (≈10^{(len(str(space))-1)}).")
    print("- Praktikoje bruteforce be papildomos info – beprasmiskas.")

    # 3) Su salt, kai salt ZINOMAS – bruteforce vis dar imanomas mazoms erdvems
    start = time.perf_counter()
    found2 = None
    for i in range(10**PIN_DIG):
        cand = f"{i:0{PIN_DIG}d}"
        if salted_hash(cand, salt) == target2:
            found2 = cand
            break
    t2 = time.perf_counter() - start
    print(f"Su ZINOMU salt bruteforce rado PIN={found2} per {t2:.4f} s, bandymu: {i+1:,}")

def hiding_menu():
    print("\n--- Negriztamumo / Hiding / Puzzle demonstracija ---")
    print("a) Sukurti commitment (HASH(input + salt))")
    print("b) Patikrinti commitment")
    print("c) Puzzle demo: bruteforce su/ be salt")
    sub = input("Pasirinkite [a/b/c]: ").strip().lower()
    if sub == "a":
        commitment_create()
    elif sub == "b":
        commitment_verify()
    elif sub == "c":
        puzzle_demo()
    else:
        print("Neteisinga pasirinktis.")

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
        print("5 - Lavinos efekto testas (100k poru, skiriasi 1 simboliu)")
        print("6 - Negriztamumo (hiding/puzzle) demonstracija – HASH(input + salt)")
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
        elif opt == '5':
            try:
                s = input("Kiek bandymų? [100000]: ").strip()
                samples = int(s) if s else 100_000
            except ValueError:
                samples = 100_000
            try:
                l = input("Vienos eilutės ilgis? [64]: ").strip()
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