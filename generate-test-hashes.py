import secrets
import string
from pathlib import Path

import bcrypt
from argon2 import PasswordHasher


OUT_DIR = Path(__file__).parent / "hashes"
OUT_DIR.mkdir(exist_ok=True)

NUM_HASHES = 20


def random_password(length: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def gen_bcrypt(cost: int) -> None:
    out = OUT_DIR / f"bcrypt-cost{cost}.txt"
    plain_out = OUT_DIR / f"bcrypt-cost{cost}-plain.txt"
    with out.open("w") as f, plain_out.open("w") as pf:
        for _ in range(NUM_HASHES):
            pw = random_password()
            digest = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=cost)).decode()
            f.write(digest + "\n")
            pf.write(pw + "\n")
    print(f"Wrote {NUM_HASHES} bcrypt cost={cost} hashes -> {out}")


def gen_argon2(m_kb: int, t: int, p: int) -> None:
    hasher = PasswordHasher(time_cost=t, memory_cost=m_kb, parallelism=p)
    label = f"m{m_kb//1024}-t{t}-p{p}"
    out = OUT_DIR / f"argon2id-{label}.txt"
    plain_out = OUT_DIR / f"argon2id-{label}-plain.txt"
    with out.open("w") as f, plain_out.open("w") as pf:
        for _ in range(NUM_HASHES):
            pw = random_password()
            digest = hasher.hash(pw)
            f.write(digest + "\n")
            pf.write(pw + "\n")
    print(f"Wrote {NUM_HASHES} argon2id {label} hashes -> {out}")


def main() -> None:
    for cost in (10, 12):
        gen_bcrypt(cost)
    gen_argon2(65536, 3, 4)
    print("\nWordlist tip: hashcat -m 3200 hashes/bcrypt-cost10.txt wordlist.txt")
    print("Argon2id  : hashcat -m 70300 hashes/argon2id-m64-t3-p4.txt wordlist.txt")


if __name__ == "__main__":
    main()
