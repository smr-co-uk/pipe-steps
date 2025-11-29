"""Tests for path-based pipeline."""

from pathlib import Path

import pytest

from pipe_steps.discover_files_step import DiscoverFilesStep
from pipe_steps.filter_by_type_step import FilterByTypeStep
from pipe_steps.path_item import PathItem
from pipe_steps.path_pipeline import PathPipeline
from pipe_steps.path_step import PathStep


@pytest.fixture
def test_directory(tmp_path: Path) -> Path:
    """Create a test directory with sample files."""
    # Create files
    (tmp_path / "file1.csv").touch()
    (tmp_path / "file2.parquet").touch()
    (tmp_path / "file3.xlsx").touch()
    (tmp_path / "readme.txt").touch()

    # Create subdirectory with files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.csv").touch()
    (subdir / "nested.parquet").touch()

    return tmp_path


class TestPathItem:
    """Test PathItem data structure."""

    def test_path_item_file(self) -> None:
        """Test creating a file path item."""
        item = PathItem(path=Path("test.csv"), item_type="file", file_type="csv")
        assert item.path == Path("test.csv")
        assert item.item_type == "file"
        assert item.file_type == "csv"

    def test_path_item_directory(self) -> None:
        """Test creating a directory path item."""
        item = PathItem(path=Path("mydir"), item_type="directory")
        assert item.path == Path("mydir")
        assert item.item_type == "directory"
        assert item.file_type is None

    def test_path_item_invalid_type(self) -> None:
        """Test that invalid item_type raises error."""
        with pytest.raises(ValueError):
            PathItem(path=Path("test"), item_type="invalid")

    def test_path_item_invalid_file_type(self) -> None:
        """Test that invalid file_type raises error."""
        with pytest.raises(ValueError):
            PathItem(path=Path("test.txt"), item_type="file", file_type="txt")  # type: ignore

    def test_path_item_directory_with_file_type(self) -> None:
        """Test that directories shouldn't have file_type."""
        with pytest.raises(ValueError):
            PathItem(path=Path("mydir"), item_type="directory", file_type="csv")  # type: ignore


class TestFilterByTypeStep:
    """Test the FilterByTypeStep."""

    def test_filter_keep_csv(self) -> None:
        """Test filtering to keep only CSV files."""
        items = [
            PathItem(path=Path("a.csv"), item_type="file", file_type="csv"),
            PathItem(path=Path("b.parquet"), item_type="file", file_type="parquet"),
            PathItem(path=Path("c.csv"), item_type="file", file_type="csv"),
        ]

        step = FilterByTypeStep("filter_csv", ["csv"])
        result = step.process(items)

        assert len(result) == 2
        assert all(item.file_type == "csv" for item in result)

    def test_filter_multiple_types(self) -> None:
        """Test filtering multiple file types."""
        items = [
            PathItem(path=Path("a.csv"), item_type="file", file_type="csv"),
            PathItem(path=Path("b.parquet"), item_type="file", file_type="parquet"),
            PathItem(path=Path("c.xlsx"), item_type="file", file_type="xlsx"),
        ]

        step = FilterByTypeStep("filter", ["csv", "parquet"])
        result = step.process(items)

        assert len(result) == 2
        assert not any(item.file_type == "xlsx" for item in result)

    def test_filter_keeps_directories(self) -> None:
        """Test that directories are always kept."""
        items = [
            PathItem(path=Path("dir1"), item_type="directory"),
            PathItem(path=Path("a.csv"), item_type="file", file_type="csv"),
            PathItem(path=Path("dir2"), item_type="directory"),
        ]

        step = FilterByTypeStep("filter", ["parquet"])  # Only keep parquet
        result = step.process(items)

        # Should have 2 directories + 0 parquet files
        assert len(result) == 2
        assert all(item.item_type == "directory" for item in result)


class TestDiscoverFilesStep:
    """Test the DiscoverFilesStep."""

    def test_discover_non_recursive(self, test_directory: Path) -> None:
        """Test discovering files without recursion."""
        items = [PathItem(path=test_directory, item_type="directory")]

        step = DiscoverFilesStep("discover", recursive=False)
        result = step.process(items)

        # Should have the directory + 3 files in root
        assert len(result) == 4  # 1 dir + 3 supported files
        file_names = [item.path.name for item in result if item.item_type == "file"]
        assert "file1.csv" in file_names
        assert "file2.parquet" in file_names
        assert "file3.xlsx" in file_names

    def test_discover_recursive(self, test_directory: Path) -> None:
        """Test discovering files with recursion."""
        items = [PathItem(path=test_directory, item_type="directory")]

        step = DiscoverFilesStep("discover", recursive=True)
        result = step.process(items)

        # Should find all files including nested
        files = [item for item in result if item.item_type == "file"]
        file_names = [item.path.name for item in files]

        assert "file1.csv" in file_names
        assert "nested.csv" in file_names
        assert "nested.parquet" in file_names

    def test_discover_keeps_files(self, test_directory: Path) -> None:
        """Test that files are kept as-is."""
        csv_file = test_directory / "file1.csv"
        items = [PathItem(path=csv_file, item_type="file", file_type="csv")]

        step = DiscoverFilesStep("discover")
        result = step.process(items)

        assert len(result) == 1
        assert result[0].path == csv_file


class TestPathPipeline:
    """Test the PathPipeline."""

    def test_pipeline_execution(self, test_directory: Path) -> None:
        """Test pipeline execution with multiple steps."""
        items = [PathItem(path=test_directory, item_type="directory")]

        pipeline = PathPipeline(
            steps=[
                DiscoverFilesStep("discover"),
                FilterByTypeStep("filter", ["csv", "parquet"]),
            ]
        )

        result = pipeline.run(items)

        # Should have the directory + filtered files
        files = [item for item in result if item.item_type == "file"]
        # Discovery found: file1.csv, file2.parquet, file3.xlsx
        # Filter kept only: file1.csv, file2.parquet (2 files)
        assert len(files) == 2
        assert all(item.file_type in ("csv", "parquet") for item in files)
