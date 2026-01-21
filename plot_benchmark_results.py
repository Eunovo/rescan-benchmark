#!/usr/bin/env python3

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
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
    # If Threads column doesn't exist, assume 1 thread (backward compatibility)
    if 'Threads' not in df.columns:
        df['Threads'] = 1
    all_data.append(df)

combined_df = pd.concat(all_data, ignore_index=True)

# Get unique values
commits = combined_df['Commit'].unique()
threads = sorted(combined_df['Threads'].unique())
intervals = sorted(combined_df['Interval'].unique())

# Set up colors for each commit
colors = plt.cm.tab10(np.linspace(0, 1, len(commits)))
commit_colors = {commit: colors[i] for i, commit in enumerate(commits)}

# Create figure with dynamic subplots based on number of thread counts
num_threads = len(threads)
fig, axes = plt.subplots(num_threads, 2, figsize=(16, 6 * num_threads))

# Handle case where there's only one thread count (axes won't be 2D array)
if num_threads == 1:
    axes = axes.reshape(1, -1)

# Plot for each thread count
for thread_idx, thread_count in enumerate(threads):
    # Filter data for this thread count
    thread_df = combined_df[combined_df['Threads'] == thread_count]
    fast_df = thread_df[thread_df['Type'] == 'Fast']
    slow_df = thread_df[thread_df['Type'] == 'Slow']

    ax_fast = axes[thread_idx, 0]
    ax_slow = axes[thread_idx, 1]

    # Plot Fast type
    for commit in commits:
        commit_data = fast_df[fast_df['Commit'] == commit]
        if len(commit_data) > 0:
            commit_data = commit_data.sort_values('Interval')
            # Replace interval 0 with 1 for log scale plotting
            x_values = commit_data['Interval'].replace(0, 1)
            ax_fast.plot(x_values, commit_data['Avg Time (us)'] / 1000,
                        marker='o', label=commit, color=commit_colors[commit],
                        linewidth=2, markersize=8)

    ax_fast.set_xlabel('Interval (blocks between payments) [log scale]', fontsize=12)
    ax_fast.set_ylabel('Average Time (ms) [log scale]', fontsize=12)
    ax_fast.set_title(f'Fast Rescan Performance ({thread_count} thread{"s" if thread_count != 1 else ""})',
                     fontsize=14, fontweight='bold')
    ax_fast.legend()
    ax_fast.grid(True, alpha=0.3)
    ax_fast.set_xscale('log')
    ax_fast.set_yscale('log')

    # Plot Slow type
    for commit in commits:
        commit_data = slow_df[slow_df['Commit'] == commit]
        if len(commit_data) > 0:
            commit_data = commit_data.sort_values('Interval')
            # Replace interval 0 with 1 for log scale plotting
            x_values = commit_data['Interval'].replace(0, 1)
            ax_slow.plot(x_values, commit_data['Avg Time (us)'] / 1000,
                        marker='o', label=commit, color=commit_colors[commit],
                        linewidth=2, markersize=8)

    ax_slow.set_xlabel('Interval (blocks between payments) [log scale]', fontsize=12)
    ax_slow.set_ylabel('Average Time (ms) [log scale]', fontsize=12)
    ax_slow.set_title(f'Slow Rescan Performance ({thread_count} thread{"s" if thread_count != 1 else ""})',
                     fontsize=14, fontweight='bold')
    ax_slow.legend()
    ax_slow.grid(True, alpha=0.3)
    ax_slow.set_xscale('log')
    ax_slow.set_yscale('log')

plt.tight_layout()
plt.savefig('benchmark_comparison.png', dpi=300, bbox_inches='tight')
print("Graph saved as 'benchmark_comparison.png'")

# Print summary statistics
print("\n=== Summary Statistics ===")
for commit in commits:
    print(f"\nCommit: {commit}")
    for thread_count in threads:
        commit_thread_df = combined_df[(combined_df['Commit'] == commit) &
                                        (combined_df['Threads'] == thread_count)]
        commit_fast = commit_thread_df[commit_thread_df['Type'] == 'Fast']
        commit_slow = commit_thread_df[commit_thread_df['Type'] == 'Slow']

        if len(commit_fast) > 0 and len(commit_slow) > 0:
            print(f"  {thread_count} thread{'s' if thread_count != 1 else ''}:")
            print(f"    Fast - Avg time: {commit_fast['Avg Time (us)'].mean() / 1000:.2f} ms")
            print(f"    Slow - Avg time: {commit_slow['Avg Time (us)'].mean() / 1000:.2f} ms")
            print(f"    Speedup: {commit_slow['Avg Time (us)'].mean() / commit_fast['Avg Time (us)'].mean():.2f}x")

plt.show()
