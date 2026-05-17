import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", "/benchmark/results"))
CHARTS_DIR = Path(os.environ.get("CHARTS_DIR", "/benchmark/charts"))
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

BCRYPT_COLOR = "#d62728"
ARGON_COLOR = "#1f77b4"
TEXT = "#1a1a1a"
BG = "#fafafa"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "font.family": "DejaVu Sans",
    "axes.edgecolor": TEXT,
    "axes.labelcolor": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "text.color": TEXT,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "--",
})


def load() -> dict:
    data = json.loads((RESULTS_DIR / "cpu-results.json").read_text())
    return data


def split_results(results):
    bcrypt_rows = [r for r in results if r["algo"] == "bcrypt"]
    argon2_rows = [r for r in results if r["algo"] == "argon2id"]
    return bcrypt_rows, argon2_rows


def plot_speed(results, out_path: Path) -> None:
    bcrypt_rows, argon2_rows = split_results(results)
    labels = [r["label"] for r in bcrypt_rows + argon2_rows]
    times = [r["ms_p50"] for r in bcrypt_rows + argon2_rows]
    colors = [BCRYPT_COLOR] * len(bcrypt_rows) + [ARGON_COLOR] * len(argon2_rows)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=160)
    bars = ax.barh(labels, times, color=colors, edgecolor=TEXT, linewidth=0.5)
    for bar, t in zip(bars, times):
        ax.text(t + max(times) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{t:.0f} ms", va="center", fontsize=10)

    ax.set_xlabel("Thời gian hash 1 password (ms, median)")
    ax.set_title("Thời gian hash trên CPU: bcrypt vs Argon2id", fontsize=13, weight="bold")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Wrote {out_path}")


def plot_memory(results, out_path: Path) -> None:
    bcrypt_rows, argon2_rows = split_results(results)
    rows = bcrypt_rows + argon2_rows
    labels = [r["label"] for r in rows]
    mems_kb = []
    for r in rows:
        if r["algo"] == "bcrypt":
            mems_kb.append(4)
        else:
            mems_kb.append(r["params"]["m_kb"])
    colors = [BCRYPT_COLOR] * len(bcrypt_rows) + [ARGON_COLOR] * len(argon2_rows)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=160)
    bars = ax.barh(labels, mems_kb, color=colors, edgecolor=TEXT, linewidth=0.5)
    ax.set_xscale("log")
    for bar, m in zip(bars, mems_kb):
        if m >= 1024:
            text = f"{m/1024:.0f} MB"
        else:
            text = f"{m} KB"
        ax.text(m * 1.1, bar.get_y() + bar.get_height() / 2, text, va="center", fontsize=10)

    ax.set_xlabel("Memory mỗi hash (KB, log scale)")
    ax.set_title("Memory footprint: vì sao GPU bottleneck", fontsize=13, weight="bold")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Wrote {out_path}")


def plot_speed_vs_memory(results, out_path: Path) -> None:
    bcrypt_rows, argon2_rows = split_results(results)

    fig, ax = plt.subplots(figsize=(10, 7), dpi=160)

    for r in bcrypt_rows:
        x = r["ms_p50"]
        y = 4
        ax.scatter(x, y, s=200, c=BCRYPT_COLOR, edgecolor=TEXT, linewidth=0.5, zorder=3)
        ax.annotate(f"cost={r['params']['cost']}", (x, y), xytext=(8, 8),
                    textcoords="offset points", fontsize=9, color=BCRYPT_COLOR)

    for r in argon2_rows:
        x = r["ms_p50"]
        y = r["params"]["m_kb"]
        ax.scatter(x, y, s=200, c=ARGON_COLOR, edgecolor=TEXT, linewidth=0.5, zorder=3)
        m_mb = r["params"]["m_kb"] // 1024
        ax.annotate(f"{m_mb}MB t={r['params']['t']} p={r['params']['p']}", (x, y),
                    xytext=(8, 8), textcoords="offset points", fontsize=9, color=ARGON_COLOR)

    ax.set_yscale("log")
    ax.set_xlabel("Thời gian hash (ms, median)")
    ax.set_ylabel("Memory mỗi hash (KB, log scale)")
    ax.set_title("Trục ẩn: memory cost không xuất hiện trong wall-clock", fontsize=13, weight="bold")

    ax.scatter([], [], s=200, c=BCRYPT_COLOR, edgecolor=TEXT, linewidth=0.5, label="bcrypt")
    ax.scatter([], [], s=200, c=ARGON_COLOR, edgecolor=TEXT, linewidth=0.5, label="Argon2id")
    ax.legend(loc="lower right", fontsize=11)

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Wrote {out_path}")


def main():
    data = load()
    results = data["results"]
    plot_speed(results, CHARTS_DIR / "cpu-speed.png")
    plot_memory(results, CHARTS_DIR / "memory-footprint.png")
    plot_speed_vs_memory(results, CHARTS_DIR / "speed-vs-memory.png")


if __name__ == "__main__":
    main()
