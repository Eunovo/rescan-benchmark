#!/usr/bin/env python3
"""Plot parallel fast-rescan speedup over single-threaded fast rescan.

Speedup = (single-threaded fast rescan time) / (fast rescan time), so > 1x means
the parallel rescan wins. The single-threaded reference is baseline's 1-thread
fast rescan for each interval (falling back to each commit's own
1-thread run when there is no baseline), so any single-thread overhead a commit
adds shows up as < 1x at 1 thread. Using one shared reference means the lines in
a panel are directly comparable: a line twice as high is twice as fast.

Layout: one panel per interval, x = thread count, one line per commit. All
panels share a linear y-axis that starts at zero.
"""

import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FixedLocator, FuncFormatter

# Chart chrome and categorical palette (fixed order, never cycled)
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"
BASELINE_COLOR = "#898781"
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                 "#e87ba4", "#008300", "#6250d6", "#e34948"]
MAX_COLS = 4

# Find all "<commit>.csv" files, skipping leftovers from the removed worst-case
# benchmark ("worstcase.<commit>.csv")
csv_files = sorted(f for f in glob.glob("*.csv") if not f.startswith("worstcase."))

if not csv_files:
    print("No CSV files found in current directory")
    exit(1)

print(f"Found {len(csv_files)} CSV files: {csv_files}")

all_data = []
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    df["Commit"] = os.path.basename(csv_file)[:-len(".csv")]
    all_data.append(df)

combined_df = pd.concat(all_data, ignore_index=True)

# Threads is "N/A" for Slow rows (a different kind of rescan, not plotted) and
# a numeric string for Fast rows.
combined_df["Threads"] = pd.to_numeric(combined_df["Threads"], errors="coerce")

fast_df = combined_df[combined_df["Type"] == "Fast"].copy()

# Single-threaded fast-rescan reference per interval
single = fast_df[fast_df["Threads"] == 1]
if "baseline" in set(fast_df["Commit"]):
    ref = (single[single["Commit"] == "baseline"]
           .set_index("Interval")["Avg Time (us)"].rename("Ref (us)"))
    fast_df = fast_df.join(ref, on="Interval")
else:
    ref = single.set_index(["Commit", "Interval"])["Avg Time (us)"].rename("Ref (us)")
    fast_df = fast_df.join(ref, on=["Commit", "Interval"])
    ref = ref.groupby("Interval").median()
fast_df["Speedup"] = fast_df["Ref (us)"] / fast_df["Avg Time (us)"]
# Spread across runs: fastest run gives the highest speedup and vice versa
fast_df["Speedup Lo"] = fast_df["Ref (us)"] / fast_df["Max Time (us)"]
fast_df["Speedup Hi"] = fast_df["Ref (us)"] / fast_df["Min Time (us)"]

# Baseline first (drawn in gray as the reference), then the rest in file order
commits = list(dict.fromkeys(combined_df["Commit"]))
if "baseline" in commits:
    commits.remove("baseline")
    commits.insert(0, "baseline")
commit_colors = {}
for commit in commits:
    if commit == "baseline":
        commit_colors[commit] = BASELINE_COLOR
    else:
        commit_colors[commit] = SERIES_COLORS[len(commit_colors) - ("baseline" in commit_colors)]

intervals = sorted(fast_df["Interval"].unique())
threads = sorted(fast_df["Threads"].unique())


def format_ms(us):
    ms = us / 1000
    if ms >= 1000:
        return f"{ms / 1000:.1f} s"
    return f"{ms:.0f} ms"


plt.rcParams.update({
    "font.family": "sans-serif",
    "text.color": INK,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
})

# One panel per interval, wrapped onto rows of at most MAX_COLS
num_cols = min(len(intervals), MAX_COLS)
num_rows = -(-len(intervals) // num_cols)
fig, axes = plt.subplots(num_rows, num_cols, figsize=(3.4 * num_cols + 0.6, 3.4 * num_rows + 1.4),
                         sharey=True, squeeze=False)
fig.patch.set_facecolor(SURFACE)
axes = axes.flatten()

y_max = max(fast_df["Speedup Hi"].max(), 1.0) * 1.08

for idx, interval in enumerate(intervals):
    ax = axes[idx]
    ax.set_facecolor(SURFACE)

    # Break-even with single-threaded fast rescan
    ax.axhline(1.0, color=INK_SECONDARY, linewidth=1, linestyle=(0, (4, 3)), zorder=1)

    for commit in commits:
        series = fast_df[(fast_df["Commit"] == commit)
                         & (fast_df["Interval"] == interval)].sort_values("Threads")
        if len(series) == 0:
            continue
        color = commit_colors[commit]
        is_baseline = commit == "baseline"
        ax.fill_between(series["Threads"], series["Speedup Lo"], series["Speedup Hi"],
                        color=color, alpha=0.12, linewidth=0, zorder=2)
        ax.plot(series["Threads"], series["Speedup"], color=color,
                linewidth=2, marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1,
                label=commit, zorder=2 if is_baseline else 3)

    ref_us = ref.get(interval)
    ax.set_title(f"interval {interval}", fontsize=11, fontweight="bold", color=INK, loc="left", pad=16)
    if ref_us is not None:
        ax.text(0, 1.02, f"1 thread: {format_ms(ref_us)}", transform=ax.transAxes,
                fontsize=8.5, color=INK_MUTED, va="bottom")

    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(FixedLocator(threads))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x)}"))
    ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.set_ylim(0, y_max)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:g}×"))
    ax.grid(True, axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(length=0, labelsize=9, labelleft=True)
    ax.set_xlabel("threads", fontsize=9)
    if idx % num_cols == 0:
        ax.set_ylabel("speedup over 1 thread", fontsize=10)

# Hide unused trailing panels on the last row
for ax in axes[len(intervals):]:
    ax.set_visible(False)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.01, 0.95), ncol=len(labels),
           frameon=False, fontsize=10, handlelength=1.8)
fig.suptitle("Parallel fast rescan speedup over single-threaded (higher is better)",
             x=0.01, ha="left", fontsize=15, fontweight="bold", color=INK)
fig.text(0.01, 0.005,
         "Interval = blocks between payments. Line = mean of runs, band = min–max run. "
         "Reference (1×) is baseline's single-threaded fast rescan.",
         fontsize=8.5, color=INK_MUTED)

fig.tight_layout(rect=(0, 0.02, 1, 0.92))
plt.savefig("benchmark_comparison.png", dpi=200, facecolor=SURFACE)
print("Graph saved as 'benchmark_comparison.png'")

# Summary: speedup over single-threaded fast rescan
print("\n=== Speedup over single-threaded fast rescan (mean of runs) ===")
table = fast_df.pivot_table(index=["Commit", "Threads"], columns="Interval", values="Speedup")
table = table.reindex([c for c in commits if c in table.index.get_level_values(0)], level=0)
table.index = table.index.set_levels(table.index.levels[1].astype(int), level=1)
print(table.apply(lambda c: c.map(lambda v: f"{v:.2f}x")).to_string())

for commit in commits:
    parallel = fast_df[(fast_df["Commit"] == commit) & (fast_df["Threads"] > 1)]
    if len(parallel) == 0:
        continue
    best = parallel.loc[parallel["Speedup"].idxmax()]
    print(f"  {commit}: geomean {np.exp(np.log(parallel['Speedup']).mean()):.2f}x over 2+ threads, "
          f"best {best['Speedup']:.2f}x (interval {best['Interval']}, {int(best['Threads'])} threads)")

plt.show()
