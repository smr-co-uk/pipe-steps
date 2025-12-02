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

    def process(self, items: list[PathItem]) -> list[PathItem]:
        """
        Filter items by file type.

        Keeps directories and files with matching types.
        """
        result: list[PathItem] = []
        for item in items:
            if item.is_dir():
                result.append(item)
            elif item.file_type in self.file_types:
                result.append(item)
        return result
