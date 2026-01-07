#!/bin/bash

# Usage: ./run_benchmark_across_commits.sh <source_dir> <commit1> <commit2> <commit3> ...
# Example: ./run_benchmark_across_commits.sh /path/to/bitcoin HEAD~3 HEAD~2 HEAD~1 HEAD

set -e

# Check if source directory and commits are provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <source_dir> <commit1> <commit2> <commit3> ..."
    echo "Example: $0 /path/to/bitcoin HEAD~3 HEAD~2 HEAD~1 HEAD"
    exit 1
fi

# Get source directory and save original directory
SOURCE_DIR="$1"
ORIGINAL_DIR=$(pwd)
shift

# Validate source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' does not exist"
    exit 1
fi

# Change to source directory
cd "$SOURCE_DIR"

# Store the original branch
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
ORIGINAL_COMMIT=$(git rev-parse HEAD)

# Create patch from current benchmark (look for it in original directory)
PATCH_FILE="$ORIGINAL_DIR/rescan_benchmark.patch"

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    git checkout "$ORIGINAL_BRANCH" 2>/dev/null || git checkout "$ORIGINAL_COMMIT"
    cd "$ORIGINAL_DIR"
}

trap cleanup EXIT

# Loop through each commit
for COMMIT in "$@"; do
    echo "=========================================="
    echo "Processing commit: $COMMIT"
    echo "=========================================="

    # Get short commit hash
    COMMIT_HASH=$(git rev-parse --short "$COMMIT")
    OUTPUT_FILE="$ORIGINAL_DIR/${COMMIT_HASH}.csv"

    # Checkout the commit
    git checkout "$COMMIT"

    # Apply patch if it exists
    if [ -n "$PATCH_FILE" ]; then
        if git apply --check "$PATCH_FILE" 2>/dev/null; then
            git apply "$PATCH_FILE"
        else
            echo "Warning: Patch does not apply cleanly to $COMMIT, skipping..."
            continue
        fi
    fi

    # Build the project
    echo "Building project..."
    if ! cmake --build build -j$(nproc); then
        echo "Error: Build failed for $COMMIT, skipping..."
        if [ -n "$PATCH_FILE" ]; then
            git apply --reverse "$PATCH_FILE"
        fi
        continue
    fi

    # Run the benchmark
    echo "Running benchmark..."
    if ./build/test/functional/rescan_benchmark.py --timeout-factor 8 --output_file="$OUTPUT_FILE"; then
        echo "Benchmark completed successfully for $COMMIT"
        echo "Results saved to $OUTPUT_FILE"
    else
        echo "Error: Benchmark failed for $COMMIT"
    fi

    # Reverse the patch
    if [ -n "$PATCH_FILE" ]; then
        git apply --reverse "$PATCH_FILE"
    fi
done

echo "=========================================="
echo "All benchmarks completed!"
echo "=========================================="