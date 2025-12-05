"""Abstract base class for graph-based path processing steps."""

from abc import ABC, abstractmethod

from .path_item_graph import PathItem


class PathStep(ABC):
    """Abstract base class for steps in a graph-based pipeline."""

    def __init__(self, name: str) -> None:
        """
        Initialize the path step.

        Args:
            name: Step name for identification
        """
        self.name = name

    @abstractmethod
    def get_input_channels(self) -> list[str]:
        """
        Declare the input channels this step expects.

        Returns:
            List of input channel names
        """
        pass

    @abstractmethod
    def get_output_channels(self) -> list[str]:
        """
        Declare the output channels this step produces.

        Returns:
            List of output channel names
        """
        pass

    @abstractmethod
    def process(self, inputs: dict[str, dict[str, PathItem]]) -> dict[str, dict[str, PathItem]]:
        """
        Process items from input channels and produce outputs to output channels.

        Args:
            inputs: Dictionary mapping input channel names to dicts of PathItems
                   e.g., {"input": {"file1": PathItem(...)}}

        Returns:
            Dictionary mapping output channel names to dicts of PathItems
            e.g., {"valid": {"file1": PathItem(...)}, "invalid": {"file2": PathItem(...)}}
        """
        pass

    def validate_io(self, inputs: dict[str, dict[str, PathItem]]) -> None:
        """
        Validate that inputs match declared input channels.

        Args:
            inputs: Input dictionary to validate

        Raises:
            ValueError: If inputs don't match declared channels
        """
        expected = set(self.get_input_channels())
        actual = set(inputs.keys())

        if expected != actual:
            raise ValueError(
                f"Step {self.name}: Expected input channels {expected}, got {actual}"
            )
