"""Batch representation for streaming large datasets."""

from dataclasses import dataclass

import polars as pl


@dataclass
class Batch:
    """Represents a chunk of data with start and end boundaries."""

    batch_id: int
    start_row: int
    end_row: int
    data: pl.DataFrame

    @property
    def size(self) -> int:
        """Number of rows in this batch."""
        return len(self.data)

    def __repr__(self) -> str:
        return f"Batch(id={self.batch_id}, rows={self.start_row}-{self.end_row}, size={self.size})"
