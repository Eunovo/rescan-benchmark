# Rescan Benchmark

Benchmarking tool for Bitcoin Core wallet rescan performance across commits.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Run benchmarks across multiple commits

```bash
./run_benchmark_across_commits.sh <bitcoin_source_dir> <commit1> <commit2> ...
```

Example:
```bash
./run_benchmark_across_commits.sh ~/bitcoin HEAD~3 HEAD~2 HEAD~1 HEAD
```

This will:
- Apply `rescan_benchmark.patch` to each commit
- Build and run the benchmark
- Save results as `<commit_hash>.csv`

### Plot results

```bash
./plot_benchmark_results.py
```

Generates `benchmark_comparison.png` comparing all CSV files in the current directory.

## Files

- `run_benchmark_across_commits.sh` - Runs benchmarks across multiple commits
- `plot_benchmark_results.py` - Plots benchmark results
- `rescan_benchmark.patch` - Benchmark test patch to apply
- `results/` - Sample benchmark results
