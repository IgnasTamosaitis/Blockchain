import random
import string
import hashlib
from collections import defaultdict
from pathlib import Path

# Random string generatorius
def random_string(length: int, rng: random.Random) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(rng.choices(alphabet, k=length))

# Hash funkcija porai
def hash_pair(s1: str, s2: str) -> str:
    data = (s1 + "|" + s2).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def main():
    rng = random.Random()

    lengths = [10, 100, 500, 1000]
    pairs = 100000
    out_file = "poros.txt"

    seen_hash_to_pair = {}
    collisions = 0
    duplicate_inputs = 0
    hash_counts = defaultdict(int)
    total_pairs = 0

    try:    
        out_file = Path(__file__).parent / "poros.txt"
        with open(out_file, "w", encoding="utf-8") as fout:
            for L in lengths:
                fout.write(f"=== Ilgis {L} ===\n")
                for _ in range(pairs):
                    s1 = random_string(L, rng)
                    s2 = random_string(L, rng)
                    fout.write(f"{s1} {s2}\n")

                    # Hash ir koliziju tikrinimas
                    h = hash_pair(s1, s2)
                    hash_counts[h] += 1
                    total_pairs += 1

                    if h not in seen_hash_to_pair:
                        seen_hash_to_pair[h] = (s1, s2)
                    else:
                        if seen_hash_to_pair[h] == (s1, s2):
                            duplicate_inputs += 1
                        else:
                            collisions += 1
                fout.write("\n")

        unique_hashes = len(seen_hash_to_pair)
        collision_rate = collisions / total_pairs if total_pairs else 0.0

        print("Sugeneruotos poros issaugotos faile:", out_file)
        print("----- Koliziju santrauka -----")
        print(f"Is viso poru:           {total_pairs:,}")
        print(f"Unikaliu hash'u:        {unique_hashes:,}")
        print(f"Pasikartojanciu poru:   {duplicate_inputs:,}  (nera koliziju)")
        print(f"Koliziju:               {collisions:,}")
        print(f"Koliziju daznis:        {collision_rate:.12f}")

    except OSError:
        print("Nepavyko atidaryti failo")

if __name__ == "__main__":
    main()