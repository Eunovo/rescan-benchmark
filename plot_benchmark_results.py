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
    all_data.append(df)

combined_df = pd.concat(all_data, ignore_index=True)

# Separate Fast and Slow types
fast_df = combined_df[combined_df['Type'] == 'Fast']
slow_df = combined_df[combined_df['Type'] == 'Slow']

# Get unique commits and intervals
commits = combined_df['Commit'].unique()
intervals = sorted(combined_df['Interval'].unique())

# Set up colors for each commit
colors = plt.cm.tab10(np.linspace(0, 1, len(commits)))
commit_colors = {commit: colors[i] for i, commit in enumerate(commits)}

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Plot Fast type
for commit in commits:
    commit_data = fast_df[fast_df['Commit'] == commit]
    commit_data = commit_data.sort_values('Interval')
    # Replace interval 0 with 1 for log scale plotting
    x_values = commit_data['Interval'].replace(0, 1)
    ax1.plot(x_values, commit_data['Avg Time (us)'] / 1000,
             marker='o', label=commit, color=commit_colors[commit], linewidth=2, markersize=8)

ax1.set_xlabel('Interval (blocks between payments) [log scale]', fontsize=12)
ax1.set_ylabel('Average Time (ms) [log scale]', fontsize=12)
ax1.set_title('Fast Rescan Performance', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xscale('log')
ax1.set_yscale('log')

# Plot Slow type
for commit in commits:
    commit_data = slow_df[slow_df['Commit'] == commit]
    commit_data = commit_data.sort_values('Interval')
    # Replace interval 0 with 1 for log scale plotting
    x_values = commit_data['Interval'].replace(0, 1)
    ax2.plot(x_values, commit_data['Avg Time (us)'] / 1000,
             marker='o', label=commit, color=commit_colors[commit], linewidth=2, markersize=8)

ax2.set_xlabel('Interval (blocks between payments) [log scale]', fontsize=12)
ax2.set_ylabel('Average Time (ms) [log scale]', fontsize=12)
ax2.set_title('Slow Rescan Performance', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xscale('log')
ax2.set_yscale('log')

plt.tight_layout()
plt.savefig('benchmark_comparison.png', dpi=300, bbox_inches='tight')
print("Graph saved as 'benchmark_comparison.png'")
