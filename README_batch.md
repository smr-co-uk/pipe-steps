# Batch Processing Pipeline with Frontier Tracking

A memory-efficient pipeline for processing datasets larger than RAM by streaming data in batches with automatic restart capability.

## When to Use

- **Large datasets** - Data larger than available memory
- **Database streaming** - Fetch data incrementally from SQL (10K-100K rows per batch)
- **Restartable pipelines** - Resume from failure without reprocessing
- **Multiple steps** - Coordinate steps processing same batch size

## Core Concepts

### Batch
A chunk of data with boundaries:
```python
Batch(batch_id=0, start_row=0, end_row=9999, data=polars_dataframe)
```

### Frontier
Tracks the last row successfully processed by ALL steps:
```
Input Batch 1 → Step 1 → Step 2 → Step 3 → Advance Frontier
Input Batch 2 → (Step 1-3) → Advance Frontier
[If step fails, frontier saved; resume from there]
```

### Batch Fetcher
Function that provides batches on demand:
```python
def batch_fetcher(batch_id: int, batch_size: int) -> Batch | None:
    """Fetch batch from SQL, file, or other source"""
    if no_more_data:
        return None
    return Batch(batch_id, start_row, end_row, data)
```

## Quick Start

```python
from pipe_steps import (
    BatchPipeline,
    DropNullsBatchStep,
    AddColumnBatchStep
)

# Define how to fetch batches
def batch_fetcher(batch_id, batch_size):
    # Fetch from SQL: rows[batch_id*batch_size : (batch_id+1)*batch_size]
    return Batch(batch_id, start_row, end_row, df_batch)

# Create pipeline
pipeline = BatchPipeline(
    steps=[
        DropNullsBatchStep("drop_nulls"),
        AddColumnBatchStep("add_feature", "value", multiplier=3),
    ],
    batch_fetcher=batch_fetcher,
    batch_size=50000,
    checkpoint_dir="./checkpoints"
)

# Process all batches
pipeline.run(resume=False)

# On failure, just call again to resume
pipeline.run(resume=True)

# Get results
result = pipeline.collect_results()
```

## Batch Steps

Create custom steps by extending `BatchStep`:

```python
from pipe_steps import BatchStep, Batch

class MyStep(BatchStep):
    def process(self, batch: Batch) -> Batch:
        # Transform batch.data
        processed = batch.data.with_columns([...])

        # Return updated batch (end_row may change)
        return Batch(
            batch_id=batch.batch_id,
            start_row=batch.start_row,
            end_row=batch.start_row + len(processed) - 1,
            data=processed
        )
```

## Frontier State

Frontier is persisted to JSON:
```json
{
  "last_completed_batch_id": 5,
  "last_completed_row": 249999,
  "total_rows_processed": 250000,
  "step_states": {"drop_nulls": 5, "add_feature": 5}
}
```

On restart, load frontier and resume from `last_completed_batch_id + 1`.

## Recovery Pattern

```python
try:
    pipeline.run(resume=False)
except Exception as e:
    # Frontier saved with last completed batch
    print(f"Failed: {e}")
    print(f"Frontier: {pipeline.get_frontier()}")

# Fix the issue and resume
pipeline.run(resume=True)  # Continues from frontier
```

## Real-World SQL Example

```python
import sqlalchemy as sa
from pipe_steps import BatchPipeline, DropNullsBatchStep

def sql_batch_fetcher(table_name, batch_size):
    engine = sa.create_engine("postgresql://...")

    def fetcher(batch_id, size):
        offset = batch_id * size
        query = f"SELECT * FROM {table_name} LIMIT {size} OFFSET {offset}"

        df = pl.read_database(query, engine)
        if len(df) == 0:
            return None

        return Batch(
            batch_id=batch_id,
            start_row=offset,
            end_row=offset + len(df) - 1,
            data=df
        )

    return fetcher

# Process directly from database
pipeline = BatchPipeline(
    steps=[DropNullsBatchStep("clean")],
    batch_fetcher=sql_batch_fetcher("large_table", batch_size=100000),
    batch_size=100000,
    checkpoint_dir="./db_checkpoints"
)

pipeline.run()
result = pipeline.collect_results()
```

## Comparison with CheckpointPipeline

| Feature | BatchPipeline | CheckpointPipeline |
|---------|---|---|
| **Memory** | Constant (batch_size) | Full dataset |
| **Data size** | Larger than RAM | Must fit in RAM |
| **Source** | Streaming (SQL) | Entire file/DF |
| **Batch coordination** | Steps in sync | Independent steps |
| **Use case** | Large datasets | Standard datasets |

## CLI

```bash
# Run demonstration
python -m pipe_steps.main_batch

# Or via installed script
batch-pipeline
```

## API Reference

**BatchPipeline:**
- `run(resume=True)` - Process all batches
- `collect_results()` - Combine all batch checkpoints
- `get_frontier()` - Get current frontier state
- `reset_frontier()` - Clear all checkpoints and restart

**Batch:**
- `batch_id` - Sequential batch number
- `start_row` - First row index
- `end_row` - Last row index
- `data` - Polars DataFrame
- `size` - Number of rows

**Frontier:**
- `last_completed_batch_id` - Last finished batch
- `total_rows_processed` - Rows at frontier
- `save(path)` - Persist to JSON
- `load(path)` - Load from JSON
