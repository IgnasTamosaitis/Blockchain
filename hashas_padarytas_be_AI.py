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
