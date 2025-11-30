#!/usr/bin/env python3
"""
Main script demonstrating the batch-based pipeline with frontier tracking.

This example shows how to use BatchPipeline for processing large datasets
that don't fit in memory by streaming data in batches from a source (e.g., SQL database).
"""

from typing import Callable

import polars as pl

from . import (
    AddColumnBatchStep,
    Batch,
    BatchPipeline,
    DropNullsBatchStep,
    FilterBatchStep,
)


def create_batch_fetcher(
    data: pl.DataFrame,
) -> Callable[[int, int], Batch | None]:
    """
    Create a batch fetcher function that streams from a DataFrame.

    In real usage, this would fetch from a SQL database or other source.
    """

    def batch_fetcher(batch_id: int, batch_size: int) -> Batch | None:
        """
        Fetch a batch of data.

        Args:
            batch_id: Which batch to fetch (0-indexed)
            batch_size: Number of rows per batch

        Returns:
            Batch object or None if no more data
        """
        start_row = batch_id * batch_size
        end_row = start_row + batch_size

        if start_row >= len(data):
            return None

        batch_data = data[start_row:end_row]
        return Batch(
            batch_id=batch_id,
            start_row=start_row,
            end_row=end_row - 1,
            data=batch_data,
        )

    return batch_fetcher


def main() -> None:
    """Demonstrate the batch pipeline with frontier tracking."""

    # Load initial data
    print("=" * 60)
    print("📂 Loading data for batch processing...")
    df = pl.read_csv("test_data/large_data.csv")
    print(f"   Loaded {len(df)} rows")
    print("\nSample data:")
    print(df.head())

    # Create batch fetcher for this data
    batch_fetcher = create_batch_fetcher(df)

    # Define pipeline steps
    print("\n" + "=" * 60)
    print("🔧 Creating batch pipeline with steps...")
    print("=" * 60)
    pipeline = BatchPipeline(
        steps=[
            DropNullsBatchStep("drop_nulls"),
            AddColumnBatchStep("add_feature1", "value", multiplier=3, new_col="feature1"),
            AddColumnBatchStep("add_feature2", "feature1", multiplier=2, new_col="feature2"),
            FilterBatchStep("filter_data", "feature1", threshold=10),
        ],
        batch_fetcher=batch_fetcher,
        batch_size=5,  # Small batch size for demo (real: 50K+)
        checkpoint_dir="./batch_checkpoints",
    )

    # First run - process all batches
    print("\n" + "=" * 60)
    print("🚀 FIRST RUN (processing all batches)...")
    print("=" * 60)
    pipeline.run(resume=False)

    # Show frontier state
    frontier = pipeline.get_frontier()
    print(f"\n✓ Frontier after first run: {frontier}")

    # Collect and display results
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    result = pipeline.collect_results()
    print(result)
    print(f"\nFinal row count: {len(result)}")
    print(f"Columns: {result.columns}")

    # Second run - resume from frontier (should be instant)
    print("\n" + "=" * 60)
    print("🚀 SECOND RUN (resume from frontier)...")
    print("=" * 60)
    pipeline.run(resume=True)
    print("✓ Resume completed (no batches reprocessed)")

    # Demonstrate failure and recovery
    print("\n" + "=" * 60)
    print("🧪 FAILURE SIMULATION")
    print("=" * 60)

    # Create a new pipeline that simulates a failure
    def batch_fetcher_with_failure(batch_id: int, batch_size: int) -> Batch | None:
        """Batch fetcher that fails on specific batch."""
        start_row = batch_id * batch_size
        end_row = start_row + batch_size

        if start_row >= len(df):
            return None

        # Simulate failure on batch 2
        if batch_id == 2:
            raise RuntimeError("⚠️  Simulated failure on batch 2")

        batch_data = df[start_row:end_row]
        return Batch(
            batch_id=batch_id,
            start_row=start_row,
            end_row=end_row - 1,
            data=batch_data,
        )

    pipeline_with_failure = BatchPipeline(
        steps=[
            DropNullsBatchStep("drop_nulls"),
            AddColumnBatchStep("add_feature1", "value", multiplier=3, new_col="feature1"),
        ],
        batch_fetcher=batch_fetcher_with_failure,
        batch_size=5,
        checkpoint_dir="./batch_checkpoints_demo",
    )

    try:
        print("\n▶ Running pipeline that will fail on batch 2...")
        pipeline_with_failure.run(resume=False)
    except RuntimeError as e:
        print(f"\n❌ {e}")
        frontier_before_recovery = pipeline_with_failure.get_frontier()
        print(f"📌 Frontier saved at: {frontier_before_recovery}")

    # Fix the fetcher and resume
    print("\n▶ Fixing the issue and resuming...")

    def batch_fetcher_fixed(batch_id: int, batch_size: int) -> Batch | None:
        """Fixed batch fetcher (no failure)."""
        start_row = batch_id * batch_size
        end_row = start_row + batch_size

        if start_row >= len(df):
            return None

        batch_data = df[start_row:end_row]
        return Batch(
            batch_id=batch_id,
            start_row=start_row,
            end_row=end_row - 1,
            data=batch_data,
        )

    pipeline_with_failure.batch_fetcher = batch_fetcher_fixed
    pipeline_with_failure.run(resume=True)

    frontier_after_recovery = pipeline_with_failure.get_frontier()
    print(f"\n✓ Recovery complete: {frontier_after_recovery}")

    print("\n" + "=" * 60)
    print("✓ All demonstrations complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
