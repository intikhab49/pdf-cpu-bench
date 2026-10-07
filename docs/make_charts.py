"""Charts for the README, read from results/results.json (nothing is typed in by hand).

    python docs/make_charts.py      -> docs/charts/*.png

Palette and styling follow Open Jev's plots.py: light surface so a PNG reads on GitHub's light
and dark themes, one highlighted series, grey for everything else, caption line top-left.
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/charts"

SURFACE, INK, INK_2, MUTED, BASELINE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7"
S1, S2, GOOD, CRITICAL = "#2a78d6", "#eb6834", "#0ca30c", "#d03b3b"

LABELS = {"mineru-basic": "MinerU (CPU tier)", "marker-fast": "marker fast", "docling": "docling",
          "marker-fast-no-ocr": "marker, no OCR", "liteparse": "liteparse",
          "liteparse-no-ocr": "liteparse, no OCR", "unstructured-hi-res": "unstructured hi_res",
          "pymupdf4llm": "pymupdf4llm", "markitdown": "markitdown"}
CATS = [("arxiv_math", "arXiv math"), ("old_scans_math", "old scans, math"), ("table_tests", "tables"),
        ("old_scans", "old scans"), ("headers_footers", "headers & footers"),
        ("multi_column", "multi column"), ("long_tiny_text", "long tiny text"), ("baseline", "baseline")]

data = json.loads((ROOT / "results/results.json").read_text())
scores, speed = data["scores"], data["speed"]
order = sorted(scores, key=lambda k: scores[k]["score"])  # ascending, for barh
leader = order[-1]


def style():
    matplotlib.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": BASELINE, "axes.linewidth": 1.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": BASELINE, "grid.alpha": 0.45, "grid.linewidth": 0.8,
        "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.titlepad": 12, "figure.dpi": 120,
    })


def finish(fig, axes, name, subtitle):
    for ax in axes:
        ax.set_axisbelow(True)
    fig.text(0.0, 1.0, subtitle, ha="left", va="bottom", fontsize=10, color=INK_2, transform=fig.transFigure)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)
    print(f"  {OUT / name}")


def scores_chart():
    fig, ax = plt.subplots(figsize=(8.4, 0.55 * len(order) + 1.8))
    ys = range(len(order))
    vals = [scores[k]["score"] for k in order]
    errs = [scores[k]["ci95"] for k in order]
    ax.barh(list(ys), vals, height=0.62, color=[S1 if k == leader else BASELINE for k in order],
            xerr=errs, error_kw={"ecolor": INK_2, "elinewidth": 1, "capsize": 3})
    for y, k, v in zip(ys, order, vals):
        ax.text(max(vals) * 1.08, y, f"{v:.1f}", va="center", fontsize=11,
                color=INK if k == leader else INK_2, fontweight="bold" if k == leader else "normal")
    ax.set_yticks(list(ys), [LABELS[k] for k in order], color=INK_2, fontsize=11)
    ax.set_xlim(0, max(vals) * 1.18)
    ax.set_xlabel("olmocr-bench score, % (macro-average of 8 categories, ±95% CI)")
    ax.set_title("Quality on 1,403 PDFs")
    ax.grid(axis="y", visible=False)
    finish(fig, [ax], "1_scores.png", "Official olmocr-bench checker, 8,413 tests. Blue is the best score.")


def speed_chart():
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    # the empty corner a light parser would have to fill
    ax.add_patch(Rectangle((0.004, 45), 1.0 - 0.004, 40, facecolor=GOOD, alpha=0.07, edgecolor=GOOD,
                           linestyle=(0, (4, 3)), linewidth=1.2, zorder=0))
    ax.text(0.0045, 83.5, "under 1 s/page and above 45%: nothing here", fontsize=9.5, color=GOOD,
            fontweight="bold", va="top")
    nudge = {"liteparse-no-ocr": (8, -12), "liteparse": (-8, 8), "marker-fast-no-ocr": (8, 4),
             "pymupdf4llm": (8, -12), "markitdown": (8, -4), "docling": (-8, 8),
             "unstructured-hi-res": (8, -12), "mineru-basic": (-8, 8), "marker-fast": (-8, 8)}
    for k in scores:
        x, y = speed[k]["median_s"], scores[k]["score"]
        lead = k == leader
        ax.scatter(x, y, s=90 if lead else 60, color=S1 if lead else INK_2, zorder=3)
        dx, dy = nudge.get(k, (8, 4))
        ax.annotate(LABELS[k], (x, y), xytext=(dx, dy), textcoords="offset points",
                    ha="left" if dx > 0 else "right", fontsize=10, color=INK if lead else INK_2,
                    fontweight="bold" if lead else "normal")
    ax.set_xscale("log")
    ax.set_xlim(0.004, 60)
    ax.set_ylim(20, 85)
    ax.set_xlabel("median seconds per page, one page at a time (log scale)")
    ax.set_ylabel("olmocr-bench score, %")
    ax.set_title("Quality vs speed on one 4-core CPU")
    finish(fig, [ax], "2_score_vs_speed.png",
           "Same runner and same 70 pages for every tool. Up and to the left is better.")


def footprint_chart():
    keys = order[::-1]  # best score first
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 0.5 * len(keys) + 1.9), sharey=True)
    ys = list(range(len(keys)))[::-1]
    inst = [speed[k]["install_mb"] / 1024 for k in keys]
    mods = [speed[k]["downloads_mb"] / 1024 for k in keys]
    ram = [speed[k]["peak_rss_mb"] / 1024 for k in keys]
    a1.barh(ys, inst, height=0.62, color=S1, label="pip install")
    a1.barh(ys, mods, left=inst, height=0.62, color=S2, label="first-run model downloads")
    for y, i, m in zip(ys, inst, mods):
        a1.text(i + m + 0.15, y, f"{i + m:.1f}", va="center", fontsize=10, color=INK_2)
    a1.set_xlabel("GB on disk")
    a1.set_title("Install + models")
    a1.legend(loc="lower right", frameon=False, fontsize=9)
    a2.barh(ys, ram, height=0.62, color=[CRITICAL if r > 8 else BASELINE for r in ram])
    for y, r in zip(ys, ram):
        a2.text(r + 0.15, y, f"{r:.1f}", va="center", fontsize=10, color=INK_2)
    a2.set_xlabel("GB, whole process tree")
    a2.set_title("Peak RAM")
    a1.set_yticks(ys, [LABELS[k] for k in keys], color=INK_2, fontsize=10)
    for ax in (a1, a2):
        ax.grid(axis="y", visible=False)
        ax.set_xlim(0, max(max(i + m for i, m in zip(inst, mods)), max(ram)) * 1.15)
    finish(fig, [a1, a2], "3_footprint.png",
           "Default `pip install` on Linux, Python 3.12. Sorted by score. Red: over 8 GB of RAM.")


def categories_chart():
    keys = order[::-1]
    grid = [[scores[k]["categories"].get(c, 0.0) for c, _ in CATS] for k in keys]
    fig, ax = plt.subplots(figsize=(10.4, 0.5 * len(keys) + 2.0))
    ax.imshow(grid, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    for i, row in enumerate(grid):
        for j, v in enumerate(row):
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=10,
                    color="white" if v > 60 else INK)
    ax.set_xticks(range(len(CATS)), [n for _, n in CATS], rotation=25, ha="right", color=INK_2, fontsize=10)
    ax.set_yticks(range(len(keys)), [LABELS[k] for k in keys], color=INK_2, fontsize=10)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Where the points are won and lost")
    finish(fig, [ax], "4_categories.png",
           "Pass rate % per olmocr-bench category. Text-layer tools score 0 on both math categories.")


if __name__ == "__main__":
    style()
    scores_chart()
    speed_chart()
    footprint_chart()
    categories_chart()
