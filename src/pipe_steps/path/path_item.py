"""Data structure for file/directory path items."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

FileType = Literal["parquet", "csv", "xlsx"]
ItemType = Literal["file", "directory"]


@dataclass
class PathItem:
    """Represents a file or directory with metadata."""

    path: Path
    item_type: ItemType
    file_type: FileType | None = None

    def __post_init__(self) -> None:
        """Validate the path item."""
        # Ensure path is a Path object
        if isinstance(self.path, str):
            self.path = Path(self.path)

        if self.item_type not in ("file", "directory"):
            raise ValueError(f"item_type must be 'file' or 'directory', got {self.item_type}")

        if self.item_type == "file" and self.file_type not in ("parquet", "csv", "xlsx"):
            raise ValueError(
                f"file_type must be 'parquet', 'csv', or 'xlsx' for files, got {self.file_type}"
            )

        if self.item_type == "directory" and self.file_type is not None:
            raise ValueError("directories should not have a file_type")

    def __repr__(self) -> str:
        return f"PathItem(path={self.path.name}, type={self.item_type}, file_type={self.file_type})"
