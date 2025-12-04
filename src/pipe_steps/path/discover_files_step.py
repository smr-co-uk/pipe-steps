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
            return FileType.PARQUET
        elif suffix == ".csv":
            return FileType.CSV
        elif suffix in (".xlsx", ".xls"):
            return FileType.XLSX
        return None

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Discover files in directories.

        Keeps files as-is and expands directories by adding new entries
        for discovered files. Directory entries are kept in the output.
        New file entries use the file path string as the key.
        """
        result: dict[str, PathItem] = {}

        for name, item in items.items():
            if item.is_file():
                # Keep files as-is
                result[name] = item
            elif item.is_dir():
                # Keep the directory
                result[name] = item

                # Find files in directory and add them with path-based keys
                pattern = "**/*" if self.recursive else "*"
                for file_path in item.path.glob(pattern):
                    if file_path.is_file():
                        file_type = self._detect_file_type(file_path)
                        if file_type:
                            # Use the file path string as the key
                            result[str(file_path)] = PathItem(
                                path=file_path,
                                file_type=file_type,
                            )

        return result
