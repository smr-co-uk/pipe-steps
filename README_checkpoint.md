# Checkpoint Pipeline for Polars

A modular checkpoint-based pipeline system for Polars DataFrames that saves intermediate results as parquet files, enabling resume-from-checkpoint functionality for long-running data processing tasks.

## Project Structure

```
src/pipe_steps/
├── __init__.py                # Package exports
├── checkpoint/                # Checkpoint Pipeline Sub-Package
│   ├── __init__.py
│   ├── polars_step.py         # PolarsStep abstract base class
│   ├── drop_nulls_step.py     # DropNullsStep implementation
│   ├── add_column_step.py     # AddColumnStep implementation
│   ├── filter_step.py         # FilterStep implementation
│   ├── checkpoint_pipeline.py # CheckpointPipeline orchestrator
│   └── main_checkpoint.py     # Example usage
└── py.typed                   # Type hints marker

tests/
├── unit/
│   ├── checkpoint/
│   │   └── test_checkpoint_pipeline.py  # Unit tests
│   └── test_example.py
└── test_data/
    └── large_data.csv         # Test dataset
```

## Features

- ✅ **Automatic Checkpointing**: Saves intermediate results after each step
- ✅ **Resume Capability**: Automatically resumes from last successful checkpoint
- ✅ **Parquet Storage**: Efficient DataFrame storage format
- ✅ **Modular Design**: Easy to extend with custom steps
- ✅ **Checkpoint Management**: Clear specific or all checkpoints
- ✅ **Progress Tracking**: Visual feedback on pipeline execution

## Installation

```bash
pip install polars pytest
```

## Quick Start

```python
import polars as pl
from pipe_steps import (
    CheckpointPipeline,
    DropNullsStep,
    AddColumnStep,
    FilterStep
)

# Define your pipeline
pipeline = CheckpointPipeline(
    steps=[
        DropNullsStep("drop_nulls"),
        AddColumnStep("add_feature", "value", multiplier=3, new_col="feature1"),
        FilterStep("filter_data", "feature1", threshold=10),
    ],
    checkpoint_dir="./checkpoints"
)

# Load data and run
df = pl.read_csv('data.csv')
result = pipeline.run(df, resume=True)
```

## Core Classes

### `PolarsStep` (Abstract Base Class)
Base class for all pipeline steps. Located in `polars_step.py`.

```python
from pipe_steps import PolarsStep
import polars as pl

class PolarsStep(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(self, df: pl.DataFrame) -> pl.DataFrame:
        pass
```

### Built-in Steps

**`DropNullsStep`**: Removes rows containing null values
```python
DropNullsStep("drop_nulls")
```

**`AddColumnStep`**: Creates a new column from calculation
```python
AddColumnStep(
    name="add_feature",
    source_col="value",
    multiplier=3,
    new_col="feature1"
)
```

**`FilterStep`**: Filters rows based on threshold
```python
FilterStep(
    name="filter",
    column="feature1",
    threshold=10
)
```

### `CheckpointPipeline`

Main pipeline orchestrator. Located in `checkpoint_pipeline.py`.

**Methods:**
- `run(df, resume=True)`: Execute pipeline with checkpointing
- `list_checkpoints()`: Show checkpoint status
- `clear_checkpoints(step_name=None)`: Clear specific or all checkpoints
- `clear_from(step_name)`: Clear checkpoints from step onwards

## Creating Custom Steps

```python
from pipe_steps import PolarsStep
import polars as pl

class MyCustomStep(PolarsStep):
    def __init__(self, name: str):
        super().__init__(name)

    def process(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns([
            pl.col("col1").str.to_uppercase().alias("col1_upper")
        ])
```

## Running the Example

```bash
# Run the demo script
python -m pipe_steps.checkpoint.main_checkpoint

# Or via installed script
checkpoint-pipeline

# Run tests
pytest tests/unit/checkpoint/test_checkpoint_pipeline.py -v

# Run tests with coverage
make coverage
```

## Test Data

The `large_data.csv` file contains 20 rows of test data:
- 4 columns: id, category, value, status
- 3 rows with null values (for testing DropNullsStep)
- Values ranging from 3-30 (for testing FilterStep)

## Usage Examples

### Basic Pipeline

```python
from pipe_steps import CheckpointPipeline, DropNullsStep
import polars as pl

pipeline = CheckpointPipeline(
    steps=[DropNullsStep("clean")],
    checkpoint_dir="./my_checkpoints"
)

df = pl.read_csv('data.csv')
result = pipeline.run(df)
```

### Resume After Failure

```python
# First run - processes steps 1-3, fails at step 4
try:
    result = pipeline.run(df, resume=False)
except Exception as e:
    print(f"Pipeline failed: {e}")

# Second run - automatically resumes from step 3
result = pipeline.run(df, resume=True)  # Fast!
```

### Force Rerun from Specific Step

```python
# Clear checkpoints from 'add_feature2' onwards
pipeline.clear_from("add_feature2")

# Run again - will reprocess from add_feature2
result = pipeline.run(df, resume=True)
```

### Check Pipeline Status

```python
pipeline.list_checkpoints()
# Output:
# 📋 Checkpoint status:
#   ✓ drop_nulls (1.6 KB)
#   ✓ add_feature1 (2.0 KB)
#   ✗ add_feature2
#   ✗ filter_data
```

## Test Coverage

The test suite includes:

- **Unit tests** for individual steps (DropNullsStep, AddColumnStep, FilterStep)
- **Integration tests** for full pipeline execution
- **Checkpoint tests** for save/load/resume functionality
- **Edge case tests** for empty pipelines and error conditions

All 14 tests pass successfully.

## Use Cases

- **Large data processing**: Process datasets that take hours, resume if interrupted
- **Iterative development**: Test later steps without reprocessing earlier ones
- **Data pipelines**: Build ETL pipelines with built-in fault tolerance
- **Feature engineering**: Create and test features incrementally

## Performance Notes

- Parquet format provides efficient compression and fast read/write
- Checkpoints allow skipping expensive recomputation
- Memory usage is controlled by processing one step at a time
- For very large datasets, consider using Polars' lazy/streaming mode

## License

MIT

## Contributing

Feel free to extend with additional step types or features!
