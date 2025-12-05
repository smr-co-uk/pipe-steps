"""Example steps demonstrating tag-based routing."""

from pathlib import Path

from .path_item_tagged import FileType, PathItem
from .path_step_tagged import PathStep, Tags


class DiscoverFilesStep(PathStep):
    """Discovers files in directories and tags them as 'discovered'."""

    def __init__(self, recursive: bool = False) -> None:
        """
        Initialize the discovery step.

        Args:
            recursive: If True, search subdirectories recursively
        """
        super().__init__("discover_files", input_tags=set())  # Process all items
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
        for discovered files. All discovered files are tagged with 'discovered'.
        """
        result: dict[str, PathItem] = {}

        for name, item in items.items():
            if item.is_file():
                # Keep files as-is, add discovered tag
                item.add_tag(Tags.DISCOVERED, self.name)
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
                            new_item = PathItem(path=file_path, file_type=file_type)
                            new_item.add_tag(Tags.DISCOVERED, self.name)
                            result[str(file_path)] = new_item

        return result


class ValidateFilesStep(PathStep):
    """Validates discovered files and tags them as 'valid' or 'invalid'."""

    def __init__(self, min_size: int = 0, max_size: int | None = None) -> None:
        """
        Initialize the validation step.

        Args:
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes (None = no limit)
        """
        super().__init__("validate_files", input_tags={Tags.DISCOVERED})
        self.min_size = min_size
        self.max_size = max_size

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Validate files based on size and existence.

        Items are tagged as 'valid' or 'invalid' based on validation rules.
        The 'discovered' tag is removed after processing.
        """
        result: dict[str, PathItem] = {}

        for name, item in items.items():
            # Remove the discovered tag
            item.remove_tag(Tags.DISCOVERED, self.name)

            # Validate
            is_valid = True
            error_tags = []

            if not item.path.exists():
                is_valid = False
                error_tags.append(Tags.MISSING)
            elif item.is_file():
                size = item.path.stat().st_size

                if size < self.min_size:
                    is_valid = False
                    error_tags.append(Tags.INVALID)
                    item.add_tag(Tags.SMALL, self.name)
                elif self.max_size and size > self.max_size:
                    is_valid = False
                    error_tags.append(Tags.INVALID)
                    item.add_tag(Tags.LARGE, self.name)

            # Tag based on validation result
            if is_valid:
                item.add_tag(Tags.VALID, self.name)
            else:
                item.add_tag(Tags.INVALID, self.name)
                for tag in error_tags:
                    item.add_tag(tag, self.name)

            result[name] = item

        return result


class ProcessValidFilesStep(PathStep):
    """Processes valid files and tags them as 'processed'."""

    def __init__(self) -> None:
        super().__init__("process_valid_files", input_tags={Tags.VALID})

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Process valid files.

        In a real implementation, this would read and process the files.
        Here we just simulate by adding a 'processed' tag.
        """
        result: dict[str, PathItem] = {}

        for name, item in items.items():
            # Simulate processing
            # In reality: read file, transform data, etc.

            # Mark as processed
            item.remove_tag(Tags.VALID, self.name)
            item.add_tag(Tags.PROCESSED, self.name)
            item.add_tag(Tags.SUCCESS, self.name)

            result[name] = item

        return result


class ErrorHandlerStep(PathStep):
    """Handles invalid files and tags them based on error type."""

    def __init__(self) -> None:
        super().__init__("error_handler", input_tags={Tags.INVALID})

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Handle invalid files.

        Logs errors and decides whether files should be retried or marked as failures.
        """
        result: dict[str, PathItem] = {}

        for name, item in items.items():
            # Check error type
            if item.has_tag(Tags.MISSING):
                # Missing files are permanent failures
                item.add_tag(Tags.ERROR, self.name)
                item.add_tag(Tags.FAILURE, self.name)
                print(f"  ERROR: {item.path} does not exist")
            elif item.has_tag(Tags.SMALL) or item.has_tag(Tags.LARGE):
                # Size issues might be retryable
                item.add_tag(Tags.ERROR, self.name)
                item.add_tag(Tags.RETRY, self.name)
                size_type = "too small" if item.has_tag(Tags.SMALL) else "too large"
                print(f"  WARNING: {item.path} is {size_type}")
            else:
                # Unknown error
                item.add_tag(Tags.ERROR, self.name)
                item.add_tag(Tags.FAILURE, self.name)
                print(f"  ERROR: {item.path} failed validation")

            result[name] = item

        return result


class FilterByTypeStep(PathStep):
    """Filters items to only include specific file types."""

    def __init__(self, file_types: list[FileType]) -> None:
        """
        Initialize the filter step.

        Args:
            file_types: List of file types to keep
        """
        super().__init__("filter_by_type", input_tags={Tags.DISCOVERED})
        self.file_types = file_types

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Filter items by file type.

        Keeps directories and files with matching types.
        Items that don't match are not included in the result.
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
