# Pipe Steps - Flexible Data Processing Pipelines

A comprehensive Python package providing three specialized pipeline systems for different data processing needs. Each pipeline type is optimized for specific use cases, from file discovery to large-scale batch processing.

## 🎯 Overview

Choose the right pipeline for your use case:

| Pipeline | Use Case | Data Size | Checkpoint | Auto-Resume |
|----------|----------|-----------|-----------|-----------|
| **Checkpoint** | Iterative development, standard data processing | Fits in RAM | ✅ After each step | ✅ Yes |
| **Batch** | Large datasets, database streaming, memory-constrained | Larger than RAM | ✅ Per batch | ✅ Yes |
| **Path** | File discovery & filtering | N/A (metadata only) | ❌ | ❌ |

## Pipeline Types

### 1. CheckpointPipeline - Resume from Step Checkpoints

For processing datasets that fit in RAM with the ability to resume from any step.

**Best for:**
- Iterative development and experimentation
- Medium-sized datasets (fit in memory)
- Fault tolerance - resume from last successful step
- Feature engineering pipelines

**Features:**
- Automatic parquet checkpoints after each step
- Resume from last completed step
- Clear specific or all checkpoints
- Quick re-runs without reprocessing

📖 **[Full Documentation](./README_checkpoint.md)**

**Quick Example:**
```python
from pipe_steps import CheckpointPipeline, DropNullsStep, AddColumnStep

pipeline = CheckpointPipeline(
    steps=[
        DropNullsStep("drop_nulls"),
        AddColumnStep("add_feature", "value", multiplier=3, new_col="feature1"),
    ],
    checkpoint_dir="./checkpoints"
)

df = pl.read_csv('data.csv')
result = pipeline.run(df, resume=True)
```

---

### 2. BatchPipeline - Stream Large Datasets with Frontier Tracking

For processing datasets larger than available RAM by streaming batches with automatic restart capability.

**Best for:**
- Large datasets (100GB+) larger than RAM
- Database streaming (SQL, APIs)
- Memory-constrained environments
- Coordinated multi-step processing
- Production data pipelines

**Features:**
- Memory-efficient batch streaming
- Frontier-based restart (resume from exact point of failure)
- All steps process same batch before advancing
- Constant memory usage regardless of data size
- Direct SQL integration

📖 **[Full Documentation](./README_batch.md)**

**Quick Example:**
```python
from pipe_steps import BatchPipeline, DropNullsBatchStep

def batch_fetcher(batch_id, batch_size):
    # Fetch from SQL database
    rows = db.execute(f"SELECT * FROM table LIMIT {batch_size} OFFSET {batch_id * batch_size}")
    return Batch(batch_id, start_row, end_row, df)

pipeline = BatchPipeline(
    steps=[DropNullsBatchStep("clean")],
    batch_fetcher=batch_fetcher,
    batch_size=50000,
    checkpoint_dir="./checkpoints"
)

pipeline.run(resume=False)
result = pipeline.collect_results()
```

---

### 3. PathPipeline - File Discovery and Filtering

For processing lists of file/directory paths through discovery and filtering steps.

**Best for:**
- Finding files in directories recursively
- Filtering files by type (csv, parquet, xlsx)
- Preprocessing before batch/data pipelines
- File organization and discovery

**Features:**
- Recursive and non-recursive discovery
- Filter by file type (csv, parquet, xlsx)
- Extendable with custom path steps
- Easy integration with other pipelines

📖 **[Full Documentation](./README_pipe.md)**

**Quick Example:**
```python
from pathlib import Path
from pipe_steps import PathPipeline, DiscoverFilesStep, FilterByTypeStep

pipeline = PathPipeline([
    DiscoverFilesStep("discover", recursive=True),
    FilterByTypeStep("filter", ["csv", "parquet"])
])

items = [PathItem(path=Path("./data"), item_type="directory")]
result = pipeline.run(items)

for item in result:
    if item.item_type == "file":
        print(f"Found: {item.path}")
```

---

## Installation

```bash
# Option 1: Install directly from GitHub using pip
pip install git+https://github.com/yourusername/pipe-steps.git

# Option 2: Clone and install with uv
git clone https://github.com/yourusername/pipe-steps.git
cd pipe-steps
uv sync

# Option 3: Clone and install in editable mode
git clone https://github.com/yourusername/pipe-steps.git
cd pipe-steps
uv pip install -e .
```

## Running Examples

Each pipeline has a demonstration script:

```bash
# Checkpoint Pipeline demo
python -m pipe_steps.main

# Batch Pipeline demo
python -m pipe_steps.main_batch

# Path Pipeline demo
python -m pipe_steps.main_pipe
```

## Core Components

### Shared Interfaces

All pipelines follow similar patterns:

- **Steps**: Abstract base classes (`PolarsStep`, `BatchStep`, `PathStep`)
- **Pipeline**: Orchestrator that sequences steps
- **Custom Steps**: Extend base classes for custom logic

### Built-in Steps

**Checkpoint Pipeline:**
- `DropNullsStep` - Remove null values
- `AddColumnStep` - Create computed columns
- `FilterStep` - Filter by threshold

**Batch Pipeline:**
- `DropNullsBatchStep` - Batch-aware null removal
- `AddColumnBatchStep` - Batch-aware column addition
- `FilterBatchStep` - Batch-aware filtering

**Path Pipeline:**
- `DiscoverFilesStep` - Find files in directories
- `FilterByTypeStep` - Filter by file type

## Decision Tree

```
Do you have a large dataset (>RAM)?
├─ YES → Batch Pipeline
│   └─ Need to stream from SQL/API?
│       ├─ YES → BatchPipeline with custom batch_fetcher
│       └─ NO → BatchPipeline with file chunking
└─ NO → Data processing pipeline needed?
    ├─ YES → Checkpoint Pipeline
    │   └─ Resume from step? → Resume capability
    └─ NO → File discovery/filtering needed?
        └─ YES → Path Pipeline
```

## Key Concepts

### Checkpoints (Checkpoint & Batch Pipelines)

Both checkpoint and batch pipelines save state to enable restarts:

- **Checkpoint Pipeline**: Saves full DataFrame after each step
- **Batch Pipeline**: Saves aggregated results and frontier JSON

Restart capability differs:
- Checkpoint: Resume from specific step
- Batch: Resume from specific batch (via frontier)

### Frontier (Batch Pipeline)

A JSON file tracking the last completed batch across all steps:

```json
{
  "last_completed_batch_id": 5,
  "last_completed_row": 249999,
  "total_rows_processed": 250000,
  "step_states": {"step1": 5, "step2": 5}
}
```

On failure, restart automatically continues from `last_completed_batch_id + 1`.

### Path Items

PathPipeline works with `PathItem` objects:

```python
PathItem(
    path=Path("data.csv"),
    item_type="file",        # "file" or "directory"
    file_type="csv"          # "csv", "parquet", "xlsx"
)
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run type checking
make typecheck

# Run linting
make lint

# Run everything
make check
```

## Project Structure

```
src/pipe_steps/
├── __init__.py                      # Package exports
│
├── checkpoint/ (Checkpoint Pipeline Sub-Package):
│   ├── __init__.py
│   ├── polars_step.py
│   ├── checkpoint_pipeline.py
│   ├── drop_nulls_step.py
│   ├── add_column_step.py
│   ├── filter_step.py
│   └── main_checkpoint.py
│
├── batch/ (Batch Pipeline Sub-Package):
│   ├── __init__.py
│   ├── batch.py
│   ├── frontier.py
│   ├── batch_step.py
│   ├── batch_pipeline.py
│   ├── drop_nulls_batch_step.py
│   ├── add_column_batch_step.py
│   ├── filter_batch_step.py
│   └── main_batch.py
│
├── path/ (Path Pipeline Sub-Package):
│   ├── __init__.py
│   ├── path_item.py
│   ├── path_step.py
│   ├── path_pipeline.py
│   ├── discover_files_step.py
│   ├── filter_by_type_step.py
│   └── main_pipe.py
│
└── py.typed                         # Type hints marker
```

## Real-World Examples

### Processing 100GB Database

```python
from pipe_steps import BatchPipeline, DropNullsBatchStep, AddColumnBatchStep

def sql_batch_fetcher(batch_id, batch_size):
    query = f"SELECT * FROM huge_table LIMIT {batch_size} OFFSET {batch_id * batch_size}"
    df = pl.read_database(query, engine)
    if len(df) == 0:
        return None
    return Batch(batch_id, batch_id * batch_size, batch_id * batch_size + len(df) - 1, df)

pipeline = BatchPipeline(
    steps=[
        DropNullsBatchStep("clean"),
        AddColumnBatchStep("features", "value", multiplier=3),
    ],
    batch_fetcher=sql_batch_fetcher,
    batch_size=100000,
    checkpoint_dir="./db_processing"
)

# Process all batches with automatic restart capability
pipeline.run(resume=False)

# On failure, just restart - picks up where it left off
pipeline.run(resume=True)

result = pipeline.collect_results()
```

### Iterative Feature Engineering

```python
from pipe_steps import CheckpointPipeline, AddColumnStep

pipeline = CheckpointPipeline(
    steps=[
        AddColumnStep("feature1", "revenue", multiplier=1.1),
        AddColumnStep("feature2", "feature1", multiplier=2),
        AddColumnStep("feature3", "feature2", multiplier=0.5),
    ],
    checkpoint_dir="./features"
)

df = pl.read_csv('sales_data.csv')

# First run: processes all 3 features
result = pipeline.run(df, resume=False)

# To test a new feature4:
pipeline.steps.append(AddColumnStep("feature4", "feature3", multiplier=1.5))

# Resumes from feature3, only computes feature4
result = pipeline.run(df, resume=True)  # Fast!
```

### Multi-File Processing

```python
from pipe_steps import PathPipeline, DiscoverFilesStep, FilterByTypeStep

# Step 1: Find all CSV and Parquet files recursively
path_pipeline = PathPipeline([
    DiscoverFilesStep("discover", recursive=True),
    FilterByTypeStep("filter", ["csv", "parquet"])
])

items = [PathItem(path=Path("./data"), item_type="directory")]
files = path_pipeline.run(items)

# Step 2: Process each file with batch pipeline
for item in files:
    df = pl.read_csv(item.path)
    # ... process with batch or checkpoint pipeline
```

## Contributing

Extend with custom steps:

```python
# Custom checkpoint step
from pipe_steps import PolarsStep

class NormalizeStep(PolarsStep):
    def process(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns([
            ((pl.col("col") - pl.col("col").mean()) / pl.col("col").std()).alias("col_norm")
        ])

# Custom batch step
from pipe_steps import BatchStep, Batch

class CustomBatchStep(BatchStep):
    def process(self, batch: Batch) -> Batch:
        processed = batch.data.with_columns([...])
        return Batch(batch.batch_id, batch.start_row, batch.start_row + len(processed) - 1, processed)

# Custom path step
from pipe_steps import PathStep

class ValidateFilesStep(PathStep):
    def process(self, items: list[PathItem]) -> list[PathItem]:
        return [item for item in items if item.path.exists()]
```

## License

MIT

## Documentation

- **Checkpoint Pipeline**: [README_checkpoint.md](./README_checkpoint.md)
- **Batch Pipeline**: [README_batch.md](./README_batch.md)
- **Path Pipeline**: [README_pipe.md](./README_pipe.md)
