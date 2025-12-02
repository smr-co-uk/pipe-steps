#!/usr/bin/env python3
"""
Main script demonstrating the PathStep pipeline for file/directory processing.

This example shows how to use PathPipeline for discovering and filtering files
by type across directories.
"""

from pathlib import Path

from . import (
    DiscoverFilesStep,
    FileType,
    FilterByTypeStep,
    PathItem,
    PathPipeline,
)


def main() -> None:
    """Demonstrate the path pipeline with file discovery and filtering."""

    # Create test directory structure
    print("=" * 60)
    print("📂 Setting up test directory structure...")
    print("=" * 60)

    test_dir = Path("./test_files")
    test_dir.mkdir(exist_ok=True)

    # Create sample files
    sample_files = [
        ("data1.csv", "CSV file 1"),
        ("data2.csv", "CSV file 2"),
        ("dataset.parquet", "Parquet dataset"),
        ("export.xlsx", "Excel export"),
        ("readme.txt", "Text file (not supported)"),
    ]

    for filename, description in sample_files:
        filepath = test_dir / filename
        filepath.write_text(description)
        print(f"  ✓ Created: {filename}")

    # Create subdirectory with more files
    subdir = test_dir / "archive"
    subdir.mkdir(exist_ok=True)
    archived_files = [
        ("old_data.csv", "Archived CSV"),
        ("backup.parquet", "Archived Parquet"),
        ("notes.txt", "Text notes"),
    ]

    for filename, description in archived_files:
        filepath = subdir / filename
        filepath.write_text(description)
        print(f"  ✓ Created: archive/{filename}")

    # Scenario 1: Discover all supported files (non-recursive)
    print("\n" + "=" * 60)
    print("🔍 SCENARIO 1: Non-recursive discovery")
    print("=" * 60)
    print(f"Searching in: {test_dir}\n")

    items = [PathItem(path=test_dir)]

    pipeline = PathPipeline(
        steps=[
            DiscoverFilesStep("discover_files", recursive=False),
        ]
    )

    result = pipeline.run(items)

    print("\nDiscovered items:")
    for item in result:
        if item.is_file():
            print(f"  📄 {item.path.name} ({item.file_type})")
        else:
            print(f"  📁 {item.path.name}/")

    # Scenario 2: Recursive discovery with filtering
    print("\n" + "=" * 60)
    print("🔍 SCENARIO 2: Recursive discovery + filter CSV/Parquet")
    print("=" * 60)
    print(f"Searching in: {test_dir}\n")

    items = [PathItem(path=test_dir)]

    pipeline = PathPipeline(
        steps=[
            DiscoverFilesStep("discover_recursive", recursive=True),
            FilterByTypeStep("filter_data", [FileType.CSV, FileType.PARQUET]),
        ]
    )

    result = pipeline.run(items)

    print("\nFiltered results (CSV/Parquet only):")
    data_files = [item for item in result if item.is_file()]
    for item in data_files:
        print(f"  📄 {item.path.relative_to(test_dir)} ({item.file_type})")

    print(f"\nTotal files found: {len(data_files)}")

    # Scenario 3: Only keep Excel files
    print("\n" + "=" * 60)
    print("🔍 SCENARIO 3: Find only Excel files")
    print("=" * 60)
    print(f"Searching in: {test_dir}\n")

    items = [PathItem(path=test_dir)]

    pipeline = PathPipeline(
        steps=[
            DiscoverFilesStep("discover_all", recursive=True),
            FilterByTypeStep("filter_xlsx", [FileType.XLSX]),
        ]
    )

    result = pipeline.run(items)

    excel_files = [item for item in result if item.is_file()]
    print(f"\nExcel files found: {len(excel_files)}")
    for item in excel_files:
        print(f"  📊 {item.path.relative_to(test_dir)}")

    # Scenario 4: Process specific items
    print("\n" + "=" * 60)
    print("🔍 SCENARIO 4: Process specific file paths")
    print("=" * 60)

    # Create items for specific files
    items = [
        PathItem(path=test_dir / "data1.csv", file_type=FileType.CSV),
        PathItem(path=test_dir / "dataset.parquet", file_type=FileType.PARQUET),
        PathItem(path=test_dir / "archive"),
    ]

    print("\nInput items:")
    for item in items:
        if item.is_file():
            print(f"  📄 {item.path.name} ({item.file_type})")
        else:
            print(f"  📁 {item.path.name}/")

    # Run discovery on the archive directory
    pipeline = PathPipeline(
        steps=[
            DiscoverFilesStep("expand_dirs", recursive=False),
            FilterByTypeStep("filter_data", [FileType.CSV, FileType.PARQUET]),
        ]
    )

    result = pipeline.run(items)

    print("\nProcessed items:")
    for item in result:
        if item.is_file():
            print(f"  📄 {item.path.name} ({item.file_type})")
        else:
            print(f"  📁 {item.path.name}/")

    # Cleanup
    print("\n" + "=" * 60)
    print("🧹 Cleanup")
    print("=" * 60)

    import shutil

    if test_dir.exists():
        shutil.rmtree(test_dir)
        print(f"✓ Removed test directory: {test_dir}")

    print("\n" + "=" * 60)
    print("✓ All demonstrations complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
