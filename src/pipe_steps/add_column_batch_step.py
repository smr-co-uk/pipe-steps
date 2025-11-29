"""Batch step that adds a calculated column."""

import polars as pl

from .batch import Batch
from .batch_step import BatchStep


class AddColumnBatchStep(BatchStep):
    """Adds a new column based on a calculation for each batch."""

    def __init__(
        self,
        name: str,
        source_col: str,
        multiplier: int = 2,
        new_col: str = "calculated",
    ) -> None:
        super().__init__(name)
        self.source_col = source_col
        self.multiplier = multiplier
        self.new_col = new_col

    def process(self, batch: Batch) -> Batch:
        processed_data = batch.data.with_columns(
            [(pl.col(self.source_col) * self.multiplier).alias(self.new_col)]
        )
        return Batch(
            batch_id=batch.batch_id,
            start_row=batch.start_row,
            end_row=batch.end_row,
            data=processed_data,
        )
