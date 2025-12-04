"""Path step that filters items by file type."""

from .path_item import FileType, PathItem
from .path_step import PathStep


class FilterByTypeStep(PathStep):
    """Filters path items to only include specific file types."""

    def __init__(self, name: str, file_types: list[FileType]) -> None:
        """
        Initialize the filter step.

        Args:
            name: Step name
            file_types: List of file types to keep (parquet, csv, xlsx)
        """
        super().__init__(name)
        self.file_types = file_types

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Filter items by file type.

        Keeps directories and files with matching types.
        Removes entries that don't match the filter criteria.
        """
        result: dict[str, PathItem] = {}

        for name, item in items.items():
            if item.is_dir():
                # Always keep directories
                result[name] = item
            elif item.file_type in self.file_types:
                # Keep files that match the filter
                result[name] = item
            # Files that don't match are omitted from result

        return result
