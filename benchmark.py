import gc
import json
import os
import resource
import secrets
import statistics
import string
import time
from pathlib import Path

import bcrypt
from argon2 import PasswordHasher
from argon2.low_level import Type, hash_secret


RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", "/benchmark/results"))
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES = int(os.environ.get("SAMPLES", "30"))
WARMUP = 3


def random_password(length: int = 16) -> bytes:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length)).encode()


def peak_rss_kb() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def reset_rss_baseline() -> int:
    gc.collect()
    return peak_rss_kb()


def measure_bcrypt(cost: int) -> dict:
    salt = bcrypt.gensalt(rounds=cost)
    for _ in range(WARMUP):
        bcrypt.hashpw(random_password(), salt)

    baseline = reset_rss_baseline()
    timings_ms = []
    for _ in range(SAMPLES):
        pw = random_password()
        t0 = time.perf_counter()
        digest = bcrypt.hashpw(pw, bcrypt.gensalt(rounds=cost))
        t1 = time.perf_counter()
        assert bcrypt.checkpw(pw, digest)
        timings_ms.append((t1 - t0) * 1000)
    peak_after = peak_rss_kb()

    return {
        "algo": "bcrypt",
        "params": {"cost": cost},
        "label": f"bcrypt cost={cost}",
        "ms_p50": round(statistics.median(timings_ms), 2),
        "ms_p95": round(sorted(timings_ms)[int(0.95 * len(timings_ms)) - 1], 2),
        "ms_mean": round(statistics.mean(timings_ms), 2),
        "ms_stdev": round(statistics.stdev(timings_ms), 2) if len(timings_ms) > 1 else 0,
        "peak_mem_kb_delta": max(0, peak_after - baseline),
        "hashes_per_sec_cpu": round(1000 / statistics.median(timings_ms), 2),
        "samples": SAMPLES,
    }


def measure_argon2(m_kb: int, t: int, p: int) -> dict:
    hasher = PasswordHasher(time_cost=t, memory_cost=m_kb, parallelism=p, hash_len=32, salt_len=16)
    for _ in range(WARMUP):
        hasher.hash(random_password().decode())

    baseline = reset_rss_baseline()
    timings_ms = []
    for _ in range(SAMPLES):
        pw = random_password().decode()
        t0 = time.perf_counter()
        digest = hasher.hash(pw)
        t1 = time.perf_counter()
        assert hasher.verify(digest, pw)
        timings_ms.append((t1 - t0) * 1000)
    peak_after = peak_rss_kb()

    return {
        "algo": "argon2id",
        "params": {"m_kb": m_kb, "t": t, "p": p},
        "label": f"argon2id m={m_kb//1024}MB t={t} p={p}",
        "ms_p50": round(statistics.median(timings_ms), 2),
        "ms_p95": round(sorted(timings_ms)[int(0.95 * len(timings_ms)) - 1], 2),
        "ms_mean": round(statistics.mean(timings_ms), 2),
        "ms_stdev": round(statistics.stdev(timings_ms), 2) if len(timings_ms) > 1 else 0,
        "peak_mem_kb_delta": max(0, peak_after - baseline),
        "hashes_per_sec_cpu": round(1000 / statistics.median(timings_ms), 2),
        "samples": SAMPLES,
    }


def main() -> None:
    from importlib.metadata import version as _ver
    argon2_ver = _ver("argon2-cffi")
    bcrypt_ver = _ver("bcrypt")
    print(f"Running benchmark with {SAMPLES} samples per config...")
    print(f"Python: {os.popen('python --version').read().strip()}")
    print(f"bcrypt: {bcrypt_ver}")
    print(f"argon2-cffi: {argon2_ver}")
    print()

    bcrypt_configs = [8, 10, 12, 14]
    argon2_configs = [
        (19456, 2, 1),
        (65536, 3, 4),
        (262144, 3, 4),
    ]

    results = []

    for cost in bcrypt_configs:
        print(f"  bcrypt cost={cost} ...", flush=True)
        r = measure_bcrypt(cost)
        results.append(r)
        print(f"    p50={r['ms_p50']}ms  throughput={r['hashes_per_sec_cpu']} H/s")

    for m, t, p in argon2_configs:
        print(f"  argon2id m={m//1024}MB t={t} p={p} ...", flush=True)
        r = measure_argon2(m, t, p)
        results.append(r)
        print(f"    p50={r['ms_p50']}ms  peak_mem={r['peak_mem_kb_delta']}KB  throughput={r['hashes_per_sec_cpu']} H/s")

    out_path = RESULTS_DIR / "cpu-results.json"
    payload = {
        "meta": {
            "samples_per_config": SAMPLES,
            "bcrypt_version": bcrypt_ver,
            "argon2_cffi_version": argon2_ver,
        },
        "results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
