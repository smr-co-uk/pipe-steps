# Path Processing Pipeline

A file/directory discovery and filtering pipeline for processing lists of paths through multiple transformation steps.

## When to Use

- **File discovery** - Find files in directories recursively or non-recursively
- **File filtering** - Filter files by type (csv, parquet, xlsx)
- **Path processing** - Transform lists of path items through multiple steps
- **File organization** - Process files before batch/data operations

## Core Concepts

### PathItem
Represents a file or directory with metadata:
```python
PathItem(
    path=Path("data.csv"),
    item_type="file",           # "file" or "directory"
    file_type="csv"             # "parquet", "csv", "xlsx" (files only)
)
```

### PathStep
Abstract base for processing path items:
```python
class CustomStep(PathStep):
    def process(self, items: list[PathItem]) -> list[PathItem]:
        # Transform items
        return modified_items
```

### PathPipeline
Orchestrates multiple steps:
```python
pipeline = PathPipeline([
    DiscoverFilesStep("find"),
    FilterByTypeStep("filter", ["csv"])
])
result = pipeline.run(items)
```

## Quick Start

```python
from pathlib import Path
from pipe_steps import PathPipeline, DiscoverFilesStep, FilterByTypeStep

# Create path items
items = [PathItem(path=Path("./data"), item_type="directory")]

# Create pipeline
pipeline = PathPipeline([
    DiscoverFilesStep("discover", recursive=True),
    FilterByTypeStep("filter", ["csv", "parquet"])
])

# Run
result = pipeline.run(items)

# Access results
for item in result:
    if item.item_type == "file":
        print(f"File: {item.path} ({item.file_type})")
```

## Built-in Steps

### DiscoverFilesStep
Finds files in directories.

```python
step = DiscoverFilesStep(
    name="discover",
    recursive=False  # True to search subdirectories
)
```

Auto-detects file types: `.csv`, `.parquet`, `.xlsx`

### FilterByTypeStep
Keeps only specified file types.

```python
step = FilterByTypeStep(
    name="filter",
    file_types=["csv", "parquet"]  # Types to keep
)
```

Directories always pass through.

## Custom Steps

```python
from pipe_steps import PathStep, PathItem

class ValidateFilesStep(PathStep):
    def process(self, items: list[PathItem]) -> list[PathItem]:
        result = []
        for item in items:
            if item.item_type == "file":
                # Check if file exists
                if item.path.exists():
                    result.append(item)
            else:
                result.append(item)
        return result

# Use it
pipeline = PathPipeline([
    ValidateFilesStep("validate"),
    FilterByTypeStep("filter", ["csv"])
])
```

## Practical Examples

### Find all data files
```python
items = [PathItem(path=Path("./data"), item_type="directory")]
pipeline = PathPipeline([
    DiscoverFilesStep("discover", recursive=True),
    FilterByTypeStep("filter", ["csv", "parquet"])
])
result = pipeline.run(items)
```

### Process specific files and expand directories
```python
items = [
    PathItem(path=Path("file1.csv"), item_type="file", file_type="csv"),
    PathItem(path=Path("./backup"), item_type="directory")
]
pipeline = PathPipeline([
    DiscoverFilesStep("expand_dirs"),
    FilterByTypeStep("keep_data", ["csv"])
])
result = pipeline.run(items)
```

### Find Excel files only
```python
items = [PathItem(path=Path("./reports"), item_type="directory")]
pipeline = PathPipeline([
    DiscoverFilesStep("discover", recursive=True),
    FilterByTypeStep("filter", ["xlsx"])
])
result = pipeline.run(items)
```

## File Type Support

| Type | Extension | Code |
|------|-----------|------|
| CSV | `.csv` | `"csv"` |
| Parquet | `.parquet` | `"parquet"` |
| Excel | `.xlsx`, `.xls` | `"xlsx"` |

Unsupported files are ignored during discovery.

## API Reference

**PathItem:**
- `path: Path` - File or directory path
- `item_type: Literal["file", "directory"]` - Type indicator
- `file_type: FileType | None` - File type (files only)

**PathStep:**
- `process(items: list[PathItem]) -> list[PathItem]` - Transform items

**PathPipeline:**
- `run(items: list[PathItem]) -> list[PathItem]` - Execute pipeline

**DiscoverFilesStep:**
- `recursive: bool` - Search subdirectories (default: False)

**FilterByTypeStep:**
- `file_types: list[FileType]` - Types to keep

## CLI

```bash
# Run demonstration
python -m pipe_steps.path.main_pipe

# Or via installed script
path-pipeline
```

## Data Flow

```
Input: list[PathItem]
  ↓
Step 1: DiscoverFilesStep (expand directories)
  ↓
Step 2: FilterByTypeStep (narrow to specific types)
  ↓
Output: list[PathItem] (transformed)
```

## Integration with Other Pipelines

Path results can feed into batch or checkpoint pipelines:

```python
from pipe_steps import PathPipeline, DiscoverFilesStep, BatchPipeline

# 1. Discover CSV files
path_pipeline = PathPipeline([
    DiscoverFilesStep("discover", recursive=True),
    FilterByTypeStep("filter", ["csv"])
])
path_items = path_pipeline.run([...])

# 2. Process them with batch pipeline
def csv_batch_fetcher(batch_id, batch_size):
    # Read from discovered paths
    ...

batch_pipeline = BatchPipeline(
    steps=[...],
    batch_fetcher=csv_batch_fetcher,
    batch_size=50000
)
batch_pipeline.run()
```
