"""Abstract base class for Polars DataFrame processing steps."""

from abc import ABC, abstractmethod
import polars as pl


class PolarsStep(ABC):
    """Abstract base class for pipeline steps"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(self, df: pl.DataFrame) -> pl.DataFrame:
        """Process the DataFrame and return the result"""
        pass
