"""Abstract base class for file/directory processing steps."""

from abc import ABC, abstractmethod

from .path_item import PathItem


class PathStep(ABC):
    """Abstract base class for steps that process file/directory paths."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Process a dictionary of named path items and return the result.

        Args:
            items: Dictionary mapping names to PathItem objects

        Returns:
            Dictionary mapping names to PathItem objects
            (may be modified, added, removed, or have keys renamed)
        """
        pass
