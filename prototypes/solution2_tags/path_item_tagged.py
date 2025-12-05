"""PathItem with tag-based routing support."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FileType(Enum):
    """Supported file types."""

    PARQUET = "parquet"
    CSV = "csv"
    XLSX = "xlsx"


@dataclass
class PathItem:
    """Represents a file or directory with metadata and routing tags."""

    path: Path
    file_type: FileType | None = None
    tags: set[str] = field(default_factory=set)
    tag_history: list[tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the path item."""
        # Ensure path is a Path object
        if isinstance(self.path, str):
            self.path = Path(self.path)

        if self.is_file() and not isinstance(self.file_type, FileType):
            raise ValueError(f"file_type must be a FileType enum for files, got {self.file_type}")

        if self.is_dir() and self.file_type is not None:
            raise ValueError("directories should not have a file_type")

    def is_file(self) -> bool:
        """Check if this item is a file."""
        return self.path.is_file()

    def is_dir(self) -> bool:
        """Check if this item is a directory."""
        return self.path.is_dir()

    def add_tag(self, tag: str, step_name: str) -> None:
        """Add a tag and record in history."""
        self.tags.add(tag)
        self.tag_history.append((step_name, tag))

    def remove_tag(self, tag: str, step_name: str) -> None:
        """Remove a tag and record in history."""
        self.tags.discard(tag)
        self.tag_history.append((step_name, f"-{tag}"))

    def has_tag(self, tag: str) -> bool:
        """Check if item has a specific tag."""
        return tag in self.tags

    def has_any_tag(self, tags: set[str]) -> bool:
        """Check if item has any of the specified tags."""
        return bool(self.tags & tags)

    def __repr__(self) -> str:
        item_type = "file" if self.is_file() else "directory"
        tags_str = ",".join(sorted(self.tags)) if self.tags else "none"
        return f"PathItem(path={self.path.name}, type={item_type}, file_type={self.file_type}, tags={{{tags_str}}})"
