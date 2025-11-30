"""Batch step that filters rows based on a threshold."""

import polars as pl

from .batch import Batch
from .batch_step import BatchStep


class FilterBatchStep(BatchStep):
    """Filters rows based on a column threshold for each batch."""

    def __init__(self, name: str, column: str, threshold: float) -> None:
        super().__init__(name)
        self.column = column
        self.threshold = threshold

    def process(self, batch: Batch) -> Batch:
        filtered_data = batch.data.filter(pl.col(self.column) > self.threshold)
        return Batch(
            batch_id=batch.batch_id,
            start_row=batch.start_row,
            end_row=batch.start_row + len(filtered_data) - 1,
            data=filtered_data,
        )
