"""Example steps for graph-based pipeline."""

from pathlib import Path

from .path_item_graph import FileType, PathItem
from .path_step_graph import PathStep


class DiscoverFilesStep(PathStep):
    """Discovers files in directories."""

    def __init__(self, recursive: bool = False) -> None:
        """
        Initialize the discovery step.

        Args:
            recursive: If True, search subdirectories recursively
        """
        super().__init__("Discover Files")
        self.recursive = recursive

    def get_input_channels(self) -> list[str]:
        return ["input"]

    def get_output_channels(self) -> list[str]:
        return ["output"]

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

    def process(
        self, inputs: dict[str, dict[str, PathItem]]
    ) -> dict[str, dict[str, PathItem]]:
        """Discover files in directories."""
        items = inputs["input"]
        result: dict[str, PathItem] = {}

        for name, item in items.items():
            if item.is_file():
                # Keep files as-is
                result[name] = item
            elif item.is_dir():
                # Keep the directory
                result[name] = item

                # Find files in directory
                pattern = "**/*" if self.recursive else "*"
                for file_path in item.path.glob(pattern):
                    if file_path.is_file():
                        file_type = self._detect_file_type(file_path)
                        if file_type:
                            result[str(file_path)] = PathItem(
                                path=file_path, file_type=file_type
                            )

        return {"output": result}


class ValidateFilesStep(PathStep):
    """Validates files and routes to valid/invalid channels."""

    def __init__(self, min_size: int = 0, max_size: int | None = None) -> None:
        """
        Initialize the validation step.

        Args:
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes (None = no limit)
        """
        super().__init__("Validate Files")
        self.min_size = min_size
        self.max_size = max_size

    def get_input_channels(self) -> list[str]:
        return ["input"]

    def get_output_channels(self) -> list[str]:
        return ["valid", "invalid"]

    def process(
        self, inputs: dict[str, dict[str, PathItem]]
    ) -> dict[str, dict[str, PathItem]]:
        """Validate files and route to appropriate channels."""
        items = inputs["input"]
        valid: dict[str, PathItem] = {}
        invalid: dict[str, PathItem] = {}

        for name, item in items.items():
            is_valid = True

            if not item.path.exists():
                is_valid = False
            elif item.is_file():
                size = item.path.stat().st_size

                if size < self.min_size:
                    is_valid = False
                elif self.max_size and size > self.max_size:
                    is_valid = False

            if is_valid:
                valid[name] = item
            else:
                invalid[name] = item

        return {"valid": valid, "invalid": invalid}


class ProcessFilesStep(PathStep):
    """Processes valid files."""

    def __init__(self, operation: str = "process") -> None:
        """
        Initialize the processing step.

        Args:
            operation: Description of the operation
        """
        super().__init__(f"Process Files ({operation})")
        self.operation = operation

    def get_input_channels(self) -> list[str]:
        return ["input"]

    def get_output_channels(self) -> list[str]:
        return ["output"]

    def process(
        self, inputs: dict[str, dict[str, PathItem]]
    ) -> dict[str, dict[str, PathItem]]:
        """Process files (simulate)."""
        items = inputs["input"]
        result: dict[str, PathItem] = {}

        for name, item in items.items():
            # Simulate processing
            print(f"  {self.operation}: {item.path.name}")
            result[name] = item

        return {"output": result}


class ErrorHandlerStep(PathStep):
    """Handles invalid files and routes to retry/failure channels."""

    def __init__(self) -> None:
        super().__init__("Error Handler")

    def get_input_channels(self) -> list[str]:
        return ["input"]

    def get_output_channels(self) -> list[str]:
        return ["retry", "failure"]

    def process(
        self, inputs: dict[str, dict[str, PathItem]]
    ) -> dict[str, dict[str, PathItem]]:
        """Handle errors and route to appropriate channels."""
        items = inputs["input"]
        retry: dict[str, PathItem] = {}
        failure: dict[str, PathItem] = {}

        for name, item in items.items():
            if not item.path.exists():
                # Missing files are permanent failures
                print(f"  FAILURE: {item.path} does not exist")
                failure[name] = item
            else:
                # Other issues might be retryable
                print(f"  RETRY: {item.path} failed validation")
                retry[name] = item

        return {"retry": retry, "failure": failure}


class FilterByTypeStep(PathStep):
    """Filters items by file type and routes to type-specific channels."""

    def __init__(self) -> None:
        super().__init__("Filter By Type")

    def get_input_channels(self) -> list[str]:
        return ["input"]

    def get_output_channels(self) -> list[str]:
        return ["csv", "parquet", "xlsx", "other"]

    def process(
        self, inputs: dict[str, dict[str, PathItem]]
    ) -> dict[str, dict[str, PathItem]]:
        """Route files to channels based on file type."""
        items = inputs["input"]
        csv_items: dict[str, PathItem] = {}
        parquet_items: dict[str, PathItem] = {}
        xlsx_items: dict[str, PathItem] = {}
        other_items: dict[str, PathItem] = {}

        for name, item in items.items():
            if item.file_type == FileType.CSV:
                csv_items[name] = item
            elif item.file_type == FileType.PARQUET:
                parquet_items[name] = item
            elif item.file_type == FileType.XLSX:
                xlsx_items[name] = item
            else:
                other_items[name] = item

        return {
            "csv": csv_items,
            "parquet": parquet_items,
            "xlsx": xlsx_items,
            "other": other_items,
        }


class MergeStep(PathStep):
    """Merges multiple input channels into one output."""

    def __init__(self, input_channels: list[str]) -> None:
        """
        Initialize the merge step.

        Args:
            input_channels: List of input channel names to merge
        """
        super().__init__(f"Merge ({len(input_channels)} inputs)")
        self._input_channels = input_channels

    def get_input_channels(self) -> list[str]:
        return self._input_channels

    def get_output_channels(self) -> list[str]:
        return ["output"]

    def process(
        self, inputs: dict[str, dict[str, PathItem]]
    ) -> dict[str, dict[str, PathItem]]:
        """Merge all inputs into one output."""
        result: dict[str, PathItem] = {}

        for channel_name, items in inputs.items():
            result.update(items)

        return {"output": result}


class SplitBySizeStep(PathStep):
    """Splits files into small/large channels based on size."""

    def __init__(self, threshold: int = 1024 * 1024) -> None:
        """
        Initialize the split step.

        Args:
            threshold: Size threshold in bytes (default 1MB)
        """
        super().__init__(f"Split By Size (<{threshold//1024}KB)")
        self.threshold = threshold

    def get_input_channels(self) -> list[str]:
        return ["input"]

    def get_output_channels(self) -> list[str]:
        return ["small", "large"]

    def process(
        self, inputs: dict[str, dict[str, PathItem]]
    ) -> dict[str, dict[str, PathItem]]:
        """Split files by size."""
        items = inputs["input"]
        small: dict[str, PathItem] = {}
        large: dict[str, PathItem] = {}

        for name, item in items.items():
            if item.is_file():
                size = item.path.stat().st_size
                if size < self.threshold:
                    small[name] = item
                else:
                    large[name] = item
            else:
                # Directories go to large
                large[name] = item

        return {"small": small, "large": large}
