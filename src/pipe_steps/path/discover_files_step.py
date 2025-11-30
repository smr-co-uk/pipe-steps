"""Path step that discovers files in directories."""

from pathlib import Path

from .path_item import FileType, PathItem
from .path_step import PathStep


class DiscoverFilesStep(PathStep):
    """Discovers files in directories and adds them to the path list."""

    def __init__(self, name: str, recursive: bool = False) -> None:
        """
        Initialize the discovery step.

        Args:
            name: Step name
            recursive: If True, search subdirectories recursively
        """
        super().__init__(name)
        self.recursive = recursive

    def _detect_file_type(self, path: Path) -> FileType | None:
        """Detect file type from extension."""
        suffix = path.suffix.lower()
        if suffix == ".parquet":
            return "parquet"
        elif suffix == ".csv":
            return "csv"
        elif suffix in (".xlsx", ".xls"):
            return "xlsx"
        return None

    def process(self, items: list[PathItem]) -> list[PathItem]:
        """
        Discover files in directories.

        Keeps files as-is and expands directories to their contents.
        """
        result: list[PathItem] = []

        for item in items:
            if item.item_type == "file":
                result.append(item)
            elif item.item_type == "directory":
                # Keep the directory
                result.append(item)

                # Find files in directory
                pattern = "**/*" if self.recursive else "*"
                for file_path in item.path.glob(pattern):
                    if file_path.is_file():
                        file_type = self._detect_file_type(file_path)
                        if file_type:
                            result.append(
                                PathItem(
                                    path=file_path,
                                    item_type="file",
                                    file_type=file_type,
                                )
                            )

        return result
