"""Tests for path-based pipeline."""

from pathlib import Path

import pytest

from pipe_steps.path import (
    DiscoverFilesStep,
    FileType,
    FilterByTypeStep,
    PathItem,
    PathPipeline,
)


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

    def test_path_item_file(self, tmp_path: Path) -> None:
        """Test creating a file path item."""
        test_file = tmp_path / "test.csv"
        test_file.touch()
        item = PathItem(path=test_file, file_type=FileType.CSV)
        assert item.path == test_file
        assert item.is_file()
        assert not item.is_dir()
        assert item.file_type == FileType.CSV

    def test_path_item_directory(self, tmp_path: Path) -> None:
        """Test creating a directory path item."""
        test_dir = tmp_path / "mydir"
        test_dir.mkdir()
        item = PathItem(path=test_dir)
        assert item.path == test_dir
        assert item.is_dir()
        assert not item.is_file()
        assert item.file_type is None

    def test_path_item_invalid_file_type(self, tmp_path: Path) -> None:
        """Test that invalid file_type raises error."""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        with pytest.raises(ValueError):
            PathItem(path=test_file, file_type="txt")  # type: ignore

    def test_path_item_directory_with_file_type(self, tmp_path: Path) -> None:
        """Test that directories shouldn't have file_type."""
        test_dir = tmp_path / "mydir"
        test_dir.mkdir()
        with pytest.raises(ValueError):
            PathItem(path=test_dir, file_type=FileType.CSV)  # type: ignore


class TestFilterByTypeStep:
    """Test the FilterByTypeStep."""

    def test_filter_keep_csv(self, tmp_path: Path) -> None:
        """Test filtering to keep only CSV files."""
        # Create test files
        (tmp_path / "a.csv").touch()
        (tmp_path / "b.parquet").touch()
        (tmp_path / "c.csv").touch()

        items = {
            "a": PathItem(path=tmp_path / "a.csv", file_type=FileType.CSV),
            "b": PathItem(path=tmp_path / "b.parquet", file_type=FileType.PARQUET),
            "c": PathItem(path=tmp_path / "c.csv", file_type=FileType.CSV),
        }

        step = FilterByTypeStep("filter_csv", [FileType.CSV])
        result = step.process(items)

        assert len(result) == 2
        assert all(item.file_type == FileType.CSV for item in result.values())

    def test_filter_multiple_types(self, tmp_path: Path) -> None:
        """Test filtering multiple file types."""
        # Create test files
        (tmp_path / "a.csv").touch()
        (tmp_path / "b.parquet").touch()
        (tmp_path / "c.xlsx").touch()

        items = {
            "a": PathItem(path=tmp_path / "a.csv", file_type=FileType.CSV),
            "b": PathItem(path=tmp_path / "b.parquet", file_type=FileType.PARQUET),
            "c": PathItem(path=tmp_path / "c.xlsx", file_type=FileType.XLSX),
        }

        step = FilterByTypeStep("filter", [FileType.CSV, FileType.PARQUET])
        result = step.process(items)

        assert len(result) == 2
        assert not any(item.file_type == FileType.XLSX for item in result.values())

    def test_filter_keeps_directories(self, tmp_path: Path) -> None:
        """Test that directories are always kept."""
        # Create test directories and file
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir2").mkdir()
        (tmp_path / "a.csv").touch()

        items = {
            "dir1": PathItem(path=tmp_path / "dir1"),
            "a": PathItem(path=tmp_path / "a.csv", file_type=FileType.CSV),
            "dir2": PathItem(path=tmp_path / "dir2"),
        }

        step = FilterByTypeStep("filter", [FileType.PARQUET])  # Only keep parquet
        result = step.process(items)

        # Should have 2 directories + 0 parquet files
        assert len(result) == 2
        assert all(item.is_dir() for item in result.values())


class TestDiscoverFilesStep:
    """Test the DiscoverFilesStep."""

    def test_discover_non_recursive(self, test_directory: Path) -> None:
        """Test discovering files without recursion."""
        items = {"test_dir": PathItem(path=test_directory)}

        step = DiscoverFilesStep("discover", recursive=False)
        result = step.process(items)

        # Should have the directory + 3 files in root
        assert len(result) == 4  # 1 dir + 3 supported files
        file_names = [item.path.name for item in result.values() if item.is_file()]
        assert "file1.csv" in file_names
        assert "file2.parquet" in file_names
        assert "file3.xlsx" in file_names

    def test_discover_recursive(self, test_directory: Path) -> None:
        """Test discovering files with recursion."""
        items = {"test_dir": PathItem(path=test_directory)}

        step = DiscoverFilesStep("discover", recursive=True)
        result = step.process(items)

        # Should find all files including nested
        files = [item for item in result.values() if item.is_file()]
        file_names = [item.path.name for item in files]

        assert "file1.csv" in file_names
        assert "nested.csv" in file_names
        assert "nested.parquet" in file_names

    def test_discover_keeps_files(self, test_directory: Path) -> None:
        """Test that files are kept as-is."""
        csv_file = test_directory / "file1.csv"
        items = {"csv": PathItem(path=csv_file, file_type=FileType.CSV)}

        step = DiscoverFilesStep("discover")
        result = step.process(items)

        assert len(result) == 1
        assert result["csv"].path == csv_file


class TestPathPipeline:
    """Test the PathPipeline."""

    def test_pipeline_execution(self, test_directory: Path) -> None:
        """Test pipeline execution with multiple steps."""
        items = {"test_dir": PathItem(path=test_directory)}

        pipeline = PathPipeline(
            steps=[
                DiscoverFilesStep("discover"),
                FilterByTypeStep("filter", [FileType.CSV, FileType.PARQUET]),
            ]
        )

        result = pipeline.run(items)

        # Should have the directory + filtered files
        files = [item for item in result.values() if item.is_file()]
        # Discovery found: file1.csv, file2.parquet, file3.xlsx
        # Filter kept only: file1.csv, file2.parquet (2 files)
        assert len(files) == 2
        assert all(item.file_type in (FileType.CSV, FileType.PARQUET) for item in files)
