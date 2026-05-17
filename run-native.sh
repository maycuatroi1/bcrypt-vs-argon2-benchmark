#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

if ! python3 -c "import bcrypt, argon2, matplotlib, psutil" 2>/dev/null; then
    echo "Installing dependencies into current Python env..."
    pip install -r requirements.txt
fi

echo "=== Environment ==="
python3 --version
python3 -c "import bcrypt; print(f'bcrypt: {bcrypt.__version__}')"
python3 -c "import argon2; print(f'argon2-cffi: {argon2.__version__}')"
echo "CPU: $(grep -m1 'model name' /proc/cpuinfo | sed 's/.*: //')"
echo "RAM: $(grep MemTotal /proc/meminfo | awk '{printf "%.1f GB\n", $2/1024/1024}')"
echo

mkdir -p results "$HERE/../charts"

RESULTS_DIR="$HERE/results" CHARTS_DIR="$HERE/../charts" python3 benchmark.py
RESULTS_DIR="$HERE/results" CHARTS_DIR="$HERE/../charts" python3 plot.py

echo
echo "=== Done ==="
echo "Results: $HERE/results/cpu-results.json"
echo "Charts : $HERE/../charts/*.png"
