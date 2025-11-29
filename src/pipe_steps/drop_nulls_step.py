"""Step that drops all rows containing null values."""

import polars as pl
from .polars_step import PolarsStep


class DropNullsStep(PolarsStep):
    """Step that drops all rows containing null values"""

    def process(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.drop_nulls()
