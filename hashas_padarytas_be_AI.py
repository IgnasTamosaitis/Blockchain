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


def hash_file(fname):
    try:
        with open(fname, "r", encoding="utf-8") as f:
            content = f.read()
        hash_string(content)
    except FileNotFoundError:
        print("Failas nerastas.")


# Meniu
while True:
    opt = input("Ar norite hash'inti faila(1) ar string(2)? (Pasirinkite 1 arba 2, q-baigti): ").strip().lower()
    if opt == '2':
        txt = input("Iveskite teksta: ")
        hash_string(txt)
    elif opt == '1':
        fn = input("Iveskite failo pavadinima: ")
        hash_file(fn)
    elif opt == 'q':
        break
    else:
        print("Neteisinga ivestis")
