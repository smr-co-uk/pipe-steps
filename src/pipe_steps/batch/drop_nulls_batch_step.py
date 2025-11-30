"""Batch step that drops rows with null values."""

from .batch import Batch
from .batch_step import BatchStep


class DropNullsBatchStep(BatchStep):
    """Drops rows containing null values from each batch."""

    def process(self, batch: Batch) -> Batch:
        cleaned_data = batch.data.drop_nulls()
        return Batch(
            batch_id=batch.batch_id,
            start_row=batch.start_row,
            end_row=batch.start_row + len(cleaned_data) - 1,
            data=cleaned_data,
        )
