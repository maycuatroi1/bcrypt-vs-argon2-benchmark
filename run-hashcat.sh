#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="$HERE/results"
mkdir -p "$OUT_DIR"

if ! command -v hashcat >/dev/null 2>&1; then
    echo "hashcat not installed. Install: sudo apt install hashcat"
    exit 1
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "nvidia-smi missing in WSL2. Make sure NVIDIA driver on Windows host is recent (CUDA-on-WSL)."
    exit 1
fi

if [ -d /usr/lib/wsl/lib ]; then
    export LD_LIBRARY_PATH="/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
fi

echo "=== Versions ==="
hashcat --version
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
echo

echo "=== Hashcat devices ==="
hashcat -I | tee "$OUT_DIR/hashcat-devices.txt"
echo

run_bench() {
    local mode="$1"
    local name="$2"
    local out="$OUT_DIR/hashcat-bench-${name}.txt"
    echo "=== Benchmark $name (mode $mode) ==="
    hashcat -b -m "$mode" --machine-readable 2>/dev/null | tee "$out" || true
    hashcat -b -m "$mode" 2>/dev/null | tee -a "$out" || true
    echo
}

run_bench 3200 "bcrypt"
run_bench 70300 "argon2id"

echo "=== Done ==="
echo "Results in $OUT_DIR/"
ls -la "$OUT_DIR/"
