"""Demo script for tag-based routing pipeline."""

from pathlib import Path

from example_steps import (
    DiscoverFilesStep,
    ErrorHandlerStep,
    ProcessValidFilesStep,
    ValidateFilesStep,
)
from path_item_tagged import PathItem
from path_pipeline_tagged import PathPipeline


def demo_basic_routing() -> None:
    """Demonstrate basic success/failure routing with tags."""
    print("=" * 70)
    print("DEMO 1: Basic Tag-Based Routing (Success/Failure)")
    print("=" * 70)

    # Create a pipeline with success/failure routing
    pipeline = PathPipeline(
        [
            DiscoverFilesStep(recursive=True),
            ValidateFilesStep(min_size=10),  # Files must be at least 10 bytes
            ProcessValidFilesStep(),  # Only processes 'valid' items
            ErrorHandlerStep(),  # Only processes 'invalid' items
        ],
        debug=True,
    )

    # Show routing structure
    pipeline.visualize_routing()

    # Start with a directory
    initial_items = {"data_dir": PathItem(path=Path("data"))}

    # Run the pipeline
    print("\n" + "=" * 70)
    print("RUNNING PIPELINE")
    print("=" * 70)
    results = pipeline.run(initial_items)

    # Show final results
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    for name, item in results.items():
        print(f"\n{name}:")
        print(f"  Path: {item.path}")
        print(f"  Tags: {item.tags}")
        print(f"  History: {item.tag_history}")


def demo_parallel_branches() -> None:
    """Demonstrate multiple parallel branches based on file type."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: Parallel Branches (File Type Routing)")
    print("=" * 70)

    from example_steps import FilterByTypeStep
    from path_item_tagged import FileType
    from path_step_tagged import PathStep, Tags

    # Create custom steps for different file types
    class ProcessCSVStep(PathStep):
        """Process CSV files."""

        def __init__(self) -> None:
            super().__init__("process_csv", input_tags={Tags.VALID})

        def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
            result = {}
            for name, item in items.items():
                if item.file_type == FileType.CSV:
                    print(f"  Processing CSV: {item.path.name}")
                    item.add_tag("csv_processed", self.name)
                    result[name] = item
            return result

    class ProcessParquetStep(PathStep):
        """Process Parquet files."""

        def __init__(self) -> None:
            super().__init__("process_parquet", input_tags={Tags.VALID})

        def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
            result = {}
            for name, item in items.items():
                if item.file_type == FileType.PARQUET:
                    print(f"  Processing Parquet: {item.path.name}")
                    item.add_tag("parquet_processed", self.name)
                    result[name] = item
            return result

    pipeline = PathPipeline(
        [
            DiscoverFilesStep(recursive=True),
            ValidateFilesStep(),
            ProcessCSVStep(),  # Processes valid CSV files
            ProcessParquetStep(),  # Processes valid Parquet files
        ],
        debug=False,
    )

    initial_items = {"data_dir": PathItem(path=Path("data"))}
    results = pipeline.run(initial_items)

    print("\nFiles processed by type:")
    csv_count = sum(1 for item in results.values() if "csv_processed" in item.tags)
    parquet_count = sum(
        1 for item in results.values() if "parquet_processed" in item.tags
    )
    print(f"  CSV files: {csv_count}")
    print(f"  Parquet files: {parquet_count}")


def demo_dynamic_routing() -> None:
    """Demonstrate dynamic routing based on file size."""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Dynamic Routing (Size-Based)")
    print("=" * 70)

    from path_step_tagged import PathStep, Tags

    class SizeClassifierStep(PathStep):
        """Classify files by size into small/medium/large."""

        def __init__(self) -> None:
            super().__init__("size_classifier", input_tags={Tags.DISCOVERED})

        def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
            result = {}
            for name, item in items.items():
                if item.is_file():
                    size = item.path.stat().st_size

                    # Dynamic routing based on size
                    if size < 1024:
                        item.add_tag("tiny", self.name)
                    elif size < 1024 * 1024:
                        item.add_tag("small", self.name)
                    elif size < 10 * 1024 * 1024:
                        item.add_tag("medium", self.name)
                    else:
                        item.add_tag("large", self.name)

                result[name] = item
            return result

    class ProcessLargeFilesStep(PathStep):
        """Special handling for large files."""

        def __init__(self) -> None:
            super().__init__("process_large", input_tags={"large"})

        def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
            for name, item in items.items():
                print(f"  Large file needs special handling: {item.path.name}")
                item.add_tag("chunked_processing", self.name)
            return items

    class ProcessSmallFilesStep(PathStep):
        """Batch processing for small files."""

        def __init__(self) -> None:
            super().__init__("process_small", input_tags={"tiny", "small"})

        def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
            print(f"  Batch processing {len(items)} small files")
            for item in items.values():
                item.add_tag("batch_processed", self.name)
            return items

    pipeline = PathPipeline(
        [
            DiscoverFilesStep(),
            SizeClassifierStep(),
            ProcessLargeFilesStep(),
            ProcessSmallFilesStep(),
        ],
        debug=True,
    )

    initial_items = {"data_dir": PathItem(path=Path("data"))}
    results = pipeline.run(initial_items)

    print("\nSize distribution:")
    for size_tag in ["tiny", "small", "medium", "large"]:
        count = sum(1 for item in results.values() if size_tag in item.tags)
        if count > 0:
            print(f"  {size_tag}: {count} files")


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
        (data_dir / "data.parquet").write_bytes(b"fake parquet data here")

        print(f"Created sample files in {data_dir}/")
        print()

    demo_basic_routing()
    demo_parallel_branches()
    demo_dynamic_routing()


if __name__ == "__main__":
    main()
