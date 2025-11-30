"""Abstract base class for batch-based pipeline steps."""

from abc import ABC, abstractmethod

from .batch import Batch


class BatchStep(ABC):
    """Abstract base class for steps that process batches of data."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def process(self, batch: Batch) -> Batch:
        """
        Process a batch of data and return the result.

        Args:
            batch: Input batch to process

        Returns:
            Processed batch (may have modified data)
        """
        pass
