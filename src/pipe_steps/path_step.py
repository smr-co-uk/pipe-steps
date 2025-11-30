"""Abstract base class for file/directory processing steps."""

from abc import ABC, abstractmethod

from .path_item import PathItem


class PathStep(ABC):
    """Abstract base class for steps that process file/directory paths."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def process(self, items: list[PathItem]) -> list[PathItem]:
        """
        Process a list of path items and return the result.

        Args:
            items: List of PathItem objects to process

        Returns:
            List of PathItem objects (may be modified, added, or filtered)
        """
        pass
