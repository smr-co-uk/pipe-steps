"""Step that adds a new column based on a calculation."""

import polars as pl
from .polars_step import PolarsStep


class AddColumnStep(PolarsStep):
    """Step that adds a new column based on a calculation"""

    def __init__(self, name: str, source_col: str, multiplier: int = 2, new_col: str = 'calculated'):
        super().__init__(name)
        self.source_col = source_col
        self.multiplier = multiplier
        self.new_col = new_col

    def process(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns([
            (pl.col(self.source_col) * self.multiplier).alias(self.new_col)
        ])
