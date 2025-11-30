"""Step that filters rows based on a column threshold."""

import polars as pl

from .polars_step import PolarsStep


class FilterStep(PolarsStep):
    """Step that filters rows based on a column threshold"""

    def __init__(self, name: str, column: str, threshold: float):
        super().__init__(name)
        self.column = column
        self.threshold = threshold

    def process(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.filter(pl.col(self.column) > self.threshold)
