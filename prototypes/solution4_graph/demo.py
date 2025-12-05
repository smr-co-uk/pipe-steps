"""Demo script for graph-based DAG pipeline."""

from pathlib import Path

from example_steps import (
    DiscoverFilesStep,
    ErrorHandlerStep,
    FilterByTypeStep,
    MergeStep,
    ProcessFilesStep,
    SplitBySizeStep,
    ValidateFilesStep,
)
from path_item_graph import PathItem
from path_pipeline_graph import PathPipeline


def demo_basic_dag() -> None:
    """Demonstrate basic success/failure routing with DAG."""
    print("=" * 70)
    print("DEMO 1: Basic DAG Routing (Success/Failure)")
    print("=" * 70)

    # Create pipeline
    pipeline = PathPipeline(debug=True)

    # Add steps
    pipeline.add_step("discover", DiscoverFilesStep(recursive=True))
    pipeline.add_step("validate", ValidateFilesStep(min_size=10))
    pipeline.add_step("process_valid", ProcessFilesStep("transform"))
    pipeline.add_step("handle_errors", ErrorHandlerStep())

    # Connect steps
    pipeline.connect("discover", "validate", "output", "input")
    pipeline.connect("validate", "process_valid", "valid", "input")
    pipeline.connect("validate", "handle_errors", "invalid", "input")

    # Visualize structure
    pipeline.visualize()

    # Validate pipeline
    errors = pipeline.validate()
    if errors:
        print("\nValidation issues:")
        for error in errors:
            print(f"  - {error}")

    # Run pipeline
    print("\n" + "=" * 70)
    print("RUNNING PIPELINE")
    print("=" * 70)

    initial_items = {"data_dir": PathItem(path=Path("data"))}
    results = pipeline.run(initial_items)

    # Show results
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    for step_id, outputs in results.items():
        print(f"\n{step_id}:")
        for channel, items in outputs.items():
            print(f"  {channel}: {len(items)} items")


def demo_parallel_branches() -> None:
    """Demonstrate parallel processing branches that merge."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: Parallel Branches with Merge")
    print("=" * 70)

    pipeline = PathPipeline(debug=True)

    # Add steps
    pipeline.add_step("discover", DiscoverFilesStep(recursive=True))
    pipeline.add_step("filter_type", FilterByTypeStep())
    pipeline.add_step("process_csv", ProcessFilesStep("CSV processing"))
    pipeline.add_step("process_parquet", ProcessFilesStep("Parquet processing"))
    pipeline.add_step("process_xlsx", ProcessFilesStep("Excel processing"))
    pipeline.add_step("merge", MergeStep(["csv", "parquet", "xlsx"]))

    # Connect steps - parallel branches
    pipeline.connect("discover", "filter_type", "output", "input")
    pipeline.connect("filter_type", "process_csv", "csv", "input")
    pipeline.connect("filter_type", "process_parquet", "parquet", "input")
    pipeline.connect("filter_type", "process_xlsx", "xlsx", "input")

    # Merge results
    pipeline.connect("process_csv", "merge", "output", "csv")
    pipeline.connect("process_parquet", "merge", "output", "parquet")
    pipeline.connect("process_xlsx", "merge", "output", "xlsx")

    # Visualize
    pipeline.visualize()

    # Validate
    errors = pipeline.validate()
    if errors:
        print("\nValidation issues:")
        for error in errors:
            print(f"  - {error}")

    # Run
    print("\n" + "=" * 70)
    print("RUNNING PIPELINE")
    print("=" * 70)

    initial_items = {"data_dir": PathItem(path=Path("data"))}
    results = pipeline.run(initial_items)

    # Show results
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    if "merge" in results and "output" in results["merge"]:
        print(f"Total merged items: {len(results['merge']['output'])}")


def demo_complex_dag() -> None:
    """Demonstrate a complex DAG with multiple splits and merges."""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Complex DAG (Size + Type Routing)")
    print("=" * 70)

    pipeline = PathPipeline(debug=True)

    # Add steps
    pipeline.add_step("discover", DiscoverFilesStep(recursive=True))
    pipeline.add_step("validate", ValidateFilesStep())
    pipeline.add_step("split_size", SplitBySizeStep(threshold=100))
    pipeline.add_step("process_small", ProcessFilesStep("batch process"))
    pipeline.add_step("process_large", ProcessFilesStep("chunked process"))
    pipeline.add_step("merge_processed", MergeStep(["small", "large"]))
    pipeline.add_step("handle_errors", ErrorHandlerStep())

    # Connect steps
    pipeline.connect("discover", "validate", "output", "input")
    pipeline.connect("validate", "split_size", "valid", "input")
    pipeline.connect("validate", "handle_errors", "invalid", "input")

    # Split and process by size
    pipeline.connect("split_size", "process_small", "small", "input")
    pipeline.connect("split_size", "process_large", "large", "input")

    # Merge processed results
    pipeline.connect("process_small", "merge_processed", "output", "small")
    pipeline.connect("process_large", "merge_processed", "output", "large")

    # Visualize
    pipeline.visualize()

    # Validate
    errors = pipeline.validate()
    if errors:
        print("\nValidation issues:")
        for error in errors:
            print(f"  - {error}")

    # Run
    print("\n" + "=" * 70)
    print("RUNNING PIPELINE")
    print("=" * 70)

    initial_items = {"data_dir": PathItem(path=Path("data"))}
    results = pipeline.run(initial_items)

    # Show results
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    for step_id in ["merge_processed", "handle_errors"]:
        if step_id in results:
            print(f"\n{step_id}:")
            for channel, items in results[step_id].items():
                print(f"  {channel}: {len(items)} items")


def demo_cycle_detection() -> None:
    """Demonstrate cycle detection."""
    print("\n\n" + "=" * 70)
    print("DEMO 4: Cycle Detection")
    print("=" * 70)

    pipeline = PathPipeline(debug=False)

    # Add steps
    pipeline.add_step("step1", ProcessFilesStep("step1"))
    pipeline.add_step("step2", ProcessFilesStep("step2"))
    pipeline.add_step("step3", ProcessFilesStep("step3"))

    # Create a cycle: step1 -> step2 -> step3 -> step1
    pipeline.connect("step1", "step2", "output", "input")
    pipeline.connect("step2", "step3", "output", "input")
    pipeline.connect("step3", "step1", "output", "input")  # Creates cycle!

    print("\nAttempting to validate pipeline with cycle...")
    errors = pipeline.validate()
    if errors:
        print("\nValidation errors (expected):")
        for error in errors:
            print(f"  - {error}")

    print("\nAttempting to run pipeline with cycle...")
    try:
        pipeline.run({"start": PathItem(path=Path("data"))})
    except ValueError as e:
        print(f"Error (expected): {e}")


def main() -> None:
    """Run all demos."""
    # Check if data directory exists
    data_dir = Path("data")
    if not data_dir.exists():
        print("Creating sample data directory...")
        data_dir.mkdir(exist_ok=True)

        # Create some sample files
        (data_dir / "small.csv").write_text("id,name\n1,test\n")
        (data_dir / "empty.csv").write_text("")
        (data_dir / "large.parquet").write_bytes(b"fake parquet data" * 100)
        (data_dir / "data.xlsx").write_bytes(b"fake excel data")

        print(f"Created sample files in {data_dir}/")
        print()

    demo_basic_dag()
    demo_parallel_branches()
    demo_complex_dag()
    demo_cycle_detection()


if __name__ == "__main__":
    main()
