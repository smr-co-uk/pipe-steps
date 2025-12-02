"""Data structure for file/directory path items."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FileType(Enum):
    """Supported file types."""

    PARQUET = "parquet"
    CSV = "csv"
    XLSX = "xlsx"


@dataclass
class PathItem:
    """Represents a file or directory with metadata."""

    path: Path
    file_type: FileType | None = None

    def __post_init__(self) -> None:
        """Validate the path item."""
        # Ensure path is a Path object
        if isinstance(self.path, str):
            self.path = Path(self.path)

        if self.is_file() and not isinstance(self.file_type, FileType):
            raise ValueError(
                f"file_type must be a FileType enum for files, got {self.file_type}"
            )

        if self.is_dir() and self.file_type is not None:
            raise ValueError("directories should not have a file_type")

    def is_file(self) -> bool:
        """Check if this item is a file."""
        return self.path.is_file()

    def is_dir(self) -> bool:
        """Check if this item is a directory."""
        return self.path.is_dir()

    def __repr__(self) -> str:
        item_type = "file" if self.is_file() else "directory"
        return f"PathItem(path={self.path.name}, type={item_type}, file_type={self.file_type})"
