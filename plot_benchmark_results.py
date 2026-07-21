#!/usr/bin/env python3

import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

# Find all CSV files
csv_files = sorted(glob.glob("*.csv"))

if not csv_files:
    print("No CSV files found in current directory")
    exit(1)

print(f"Found {len(csv_files)} CSV files: {csv_files}")

# Read all CSV files and combine data
all_data = []
for csv_file in csv_files:
    commit_hash = csv_file.replace(".csv", "")
    df = pd.read_csv(csv_file)
    df['Commit'] = commit_hash
    all_data.append(df)

combined_df = pd.concat(all_data, ignore_index=True)

# Threads is "N/A" for Slow rows (Slow doesn't depend on thread count) and a
# numeric string for Fast rows.
combined_df['Threads'] = pd.to_numeric(combined_df['Threads'], errors='coerce')

fast_df = combined_df[combined_df['Type'] == 'Fast']
slow_df = combined_df[combined_df['Type'] == 'Slow']

commits = combined_df['Commit'].unique()
threads = sorted(fast_df['Threads'].unique())

commit_colors = {commit: cm.tab10(i / max(len(commits), 1)) for i, commit in enumerate(commits)}

# One plot for Slow, plus one Fast plot per thread count, laid out in a
# 2-column grid
num_plots = 1 + len(threads)
num_rows = (num_plots + 1) // 2
fig, axes = plt.subplots(num_rows, 2, figsize=(16, 6 * num_rows))
axes = axes.flatten()

max_y = max(combined_df['Avg Time (us)'].max() / 1000, 1)

# Plot Slow type: one line per commit (thread-independent)
ax_slow = axes[0]
for commit in commits:
    series = slow_df[slow_df['Commit'] == commit]
    if len(series) == 0:
        continue
    series = series.sort_values('Interval')
    # Replace interval 0 with 1 for log scale plotting
    x_values = series['Interval'].replace(0, 1)
    ax_slow.plot(x_values, series['Avg Time (us)'] / 1000,
                 marker='o', label=commit, color=commit_colors[commit],
                 linewidth=2, markersize=8)

ax_slow.set_xlabel('Interval (blocks between payments) [log scale]', fontsize=12)
ax_slow.set_ylabel('Average Time (ms) [log scale]', fontsize=12)
ax_slow.set_title('Slow Rescan Performance', fontsize=14, fontweight='bold')
ax_slow.legend()
ax_slow.grid(True, alpha=0.3)
ax_slow.set_xscale('log')
ax_slow.set_yscale('log')
ax_slow.set_ylim(top=max_y)

# Plot Fast type: one subplot per thread count, one line per commit
for thread_idx, thread in enumerate(threads):
    ax_fast = axes[1 + thread_idx]
    for commit in commits:
        series = fast_df[(fast_df['Commit'] == commit) & (fast_df['Threads'] == thread)]
        if len(series) == 0:
            continue
        series = series.sort_values('Interval')
        x_values = series['Interval'].replace(0, 1)
        ax_fast.plot(x_values, series['Avg Time (us)'] / 1000,
                     marker='o', label=commit, color=commit_colors[commit],
                     linewidth=2, markersize=8)

    ax_fast.set_xlabel('Interval (blocks between payments) [log scale]', fontsize=12)
    ax_fast.set_ylabel('Average Time (ms) [log scale]', fontsize=12)
    ax_fast.set_title(f'Fast Rescan Performance ({int(thread)} thread{"s" if thread != 1 else ""})',
                       fontsize=14, fontweight='bold')
    ax_fast.legend()
    ax_fast.grid(True, alpha=0.3)
    ax_fast.set_xscale('log')
    ax_fast.set_yscale('log')
    ax_fast.set_ylim(top=max_y)

# Hide any unused trailing subplot (odd number of plots on a 2-column grid)
for ax in axes[num_plots:]:
    ax.set_visible(False)

plt.tight_layout()
plt.savefig('benchmark_comparison.png', dpi=300, bbox_inches='tight')
print("Graph saved as 'benchmark_comparison.png'")

# Print summary statistics
print("\n=== Summary Statistics ===")
for commit in commits:
    print(f"\nCommit: {commit}")
    commit_slow = slow_df[slow_df['Commit'] == commit]
    if len(commit_slow) > 0:
        print(f"  Slow - Avg time: {commit_slow['Avg Time (us)'].mean() / 1000:.2f} ms")

    for thread in threads:
        commit_fast = fast_df[(fast_df['Commit'] == commit) & (fast_df['Threads'] == thread)]
        if len(commit_fast) > 0:
            print(f"  {int(thread)} thread{'s' if thread != 1 else ''}:")
            print(f"    Fast - Avg time: {commit_fast['Avg Time (us)'].mean() / 1000:.2f} ms")
            if len(commit_slow) > 0:
                print(f"    Speedup: {commit_slow['Avg Time (us)'].mean() / commit_fast['Avg Time (us)'].mean():.2f}x")

plt.show()
