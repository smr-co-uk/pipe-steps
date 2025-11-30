#!/usr/bin/env python3
"""
Main script demonstrating the checkpoint pipeline usage
"""

import polars as pl

from . import AddColumnStep, CheckpointPipeline, DropNullsStep, FilterStep


def main() -> None:
    """Demonstrate the checkpoint pipeline with various scenarios"""

    # Define your pipeline steps
    pipeline = CheckpointPipeline(
        steps=[
            DropNullsStep("drop_nulls"),
            AddColumnStep("add_feature1", "value", multiplier=3, new_col="feature1"),
            AddColumnStep("add_feature2", "feature1", multiplier=2, new_col="feature2"),
            FilterStep("filter_data", "feature1", threshold=10),
        ],
        checkpoint_dir="./data_checkpoints",
    )

    # Load your initial data
    print("=" * 60)
    print("📂 Loading initial data...")
    df = pl.read_csv("test_data/large_data.csv")
    print(f"   Loaded {len(df)} rows")
    print("\nInitial data:")
    print(df)

    # First run - processes all steps and saves checkpoints
    print("\n" + "=" * 60)
    print("🚀 FIRST RUN (processing all steps)...")
    print("=" * 60)
    result = pipeline.run(df, resume=False)
    print("\nFinal result:")
    print(result)

    # Check what's been completed
    pipeline.list_checkpoints()

    # Second run - automatically resumes from last checkpoint (very fast!)
    print("\n" + "=" * 60)
    print("🚀 SECOND RUN (using checkpoints - should be instant)...")
    print("=" * 60)
    result = pipeline.run(df, resume=True)

    # Force rerun from specific step
    print("\n" + "=" * 60)
    print("🔧 Clearing checkpoints from 'add_feature2' onwards...")
    print("=" * 60)
    pipeline.clear_from("add_feature2")
    pipeline.list_checkpoints()

    print("\n🚀 Running again (will reprocess from add_feature2)...")
    result = pipeline.run(df, resume=True)

    # Show final result details
    print("\n" + "=" * 60)
    print("📊 FINAL RESULT DETAILS")
    print("=" * 60)
    print(result)
    print(f"\nFinal row count: {len(result)}")
    print(f"Columns: {result.columns}")

    # Clean up for next test
    print("\n" + "=" * 60)
    print("🧹 Cleanup")
    print("=" * 60)
    pipeline.clear_checkpoints()
    print("All checkpoints cleared. Ready for next test!")


if __name__ == "__main__":
    main()
