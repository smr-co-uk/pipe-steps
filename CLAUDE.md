# CLAUDE.md - Project Context for AI Assistants

## Project Overview

**pipe-steps** is a Python package providing three specialized pipeline systems for different data processing needs. The project is designed with modularity, type safety, and fault tolerance in mind.

### Three Pipeline Types

1. **CheckpointPipeline** (`pipe_steps.checkpoint`)
   - For in-memory data processing with step-level checkpointing
   - Resumes from last completed step on failure
   - Uses Parquet files for checkpoints
   - Best for datasets that fit in RAM

2. **BatchPipeline** (`pipe_steps.batch`)
   - For streaming large datasets that don't fit in RAM
   - Uses frontier-based tracking to resume from exact batch
   - Coordinated multi-step batch processing
   - Can stream from SQL, APIs, or files

3. **PathPipeline** (`pipe_steps.path`)
   - For file discovery and filtering
   - Works with PathItem metadata (not actual file contents)
   - No checkpointing (stateless operations)
   - Used as preprocessing for other pipelines

## Architecture

### Design Patterns

- **Template Method Pattern**: Each pipeline type has an abstract base step class (`PolarsStep`, `BatchStep`, `PathStep`) with a `process()` method that subclasses implement
- **Strategy Pattern**: Different pipeline strategies for different use cases (checkpoint vs batch vs path)
- **Checkpoint Pattern**: Save intermediate state to enable restarts

### Core Components

```
Step (Abstract Base) -> Concrete Steps -> Pipeline
```

Each pipeline follows this structure:
1. Abstract step class defines interface
2. Concrete step implementations
3. Pipeline orchestrator that runs steps sequentially

### Package Organization

The codebase is organized into three sub-packages under `src/pipe_steps/`:

#### `checkpoint/` - Checkpoint Pipeline
- `polars_step.py` - Abstract base class for Polars DataFrame steps
- `checkpoint_pipeline.py` - Pipeline orchestrator with parquet checkpointing
- Concrete steps: `drop_nulls_step.py`, `add_column_step.py`, `filter_step.py`
- `main_checkpoint.py` - Demo script

#### `batch/` - Batch Pipeline
- `batch.py` - Batch data class
- `batch_step.py` - Abstract base class for batch steps
- `frontier.py` - Tracks last completed batch across all steps
- `batch_pipeline.py` - Pipeline orchestrator with frontier tracking
- Concrete steps: `drop_nulls_batch_step.py`, `add_column_batch_step.py`, `filter_batch_step.py`
- `main_batch.py` - Demo script

#### `path/` - Path Pipeline
- `path_item.py` - PathItem dataclass (path + metadata)
- `path_step.py` - Abstract base class for path steps
- `path_pipeline.py` - Pipeline orchestrator (no checkpointing)
- Concrete steps: `discover_files_step.py`, `filter_by_type_step.py`
- `main_pipe.py` - Demo script

### Key Concepts

#### Checkpoints (Checkpoint Pipeline)
- Saved as Parquet files in `checkpoint_dir/{step_name}.parquet`
- Entire DataFrame saved after each step completes
- On resume, pipeline loads last checkpoint and skips completed steps
- Resume logic: Check which steps have checkpoints, start from first missing

#### Frontier (Batch Pipeline)
- JSON file tracking progress: `checkpoint_dir/frontier.json`
- Structure:
  ```json
  {
    "last_completed_batch_id": 5,
    "last_completed_row": 249999,
    "total_rows_processed": 250000,
    "step_states": {"step1": 5, "step2": 5}
  }
  ```
- All steps process same batch before advancing (coordinated)
- On resume, starts from `last_completed_batch_id + 1`
- Batch results saved as `checkpoint_dir/{step_name}_batch_{batch_id}.parquet`

#### PathItem
- Dataclass representing file/directory metadata
- Fields: `path: Path`, `item_type: str`, `file_type: str | None`
- `item_type` can be "file" or "directory"
- `file_type` can be "csv", "parquet", "xlsx", or None

### Type Safety

- Python 3.12+ with full type hints
- `py.typed` marker for PEP 561 compliance
- Strict mypy and pyright checking enabled
- `disallow_untyped_defs = true` in mypy config
- `typeCheckingMode = "strict"` in pyright config

### Dependencies

- **polars**: DataFrame library (with openpyxl for Excel support)
- **pytest**: Testing framework
- **mypy/pyright**: Type checking
- **black/isort**: Code formatting

## Code Conventions

### File Naming
- Snake case: `checkpoint_pipeline.py`, `drop_nulls_step.py`
- Step classes end with "Step": `DropNullsStep`, `AddColumnStep`
- Pipeline classes end with "Pipeline": `CheckpointPipeline`, `BatchPipeline`

### Class Naming
- PascalCase for classes
- Abstract base classes: `PolarsStep`, `BatchStep`, `PathStep`
- Concrete implementations describe what they do: `DropNullsStep`, `FilterByTypeStep`

### Imports
- All main classes re-exported from sub-package `__init__.py`
- Can import from either location:
  ```python
  from pipe_steps import CheckpointPipeline  # Re-export
  from pipe_steps.checkpoint import CheckpointPipeline  # Direct
  ```

### Testing
- Tests in `tests/unit/` directory
- Pytest with `pythonpath = "src"` configured
- Coverage tracking available

## Development Workflow

### Running Tests
```bash
make test          # Run all tests
make coverage      # Run with coverage report
make typecheck     # Run mypy and pyright
make lint          # Run black and isort checks
make check         # Run all checks
```

### Running Examples
```bash
python -m pipe_steps.checkpoint.main_checkpoint
python -m pipe_steps.batch.main_batch
python -m pipe_steps.path.main_pipe
```

### CLI Commands
```bash
checkpoint-pipeline  # Run checkpoint demo
batch-pipeline       # Run batch demo
path-pipeline        # Run path demo
```

## Common Tasks

### Adding a New Step

1. **Checkpoint Pipeline Step**:
   - Extend `PolarsStep` from `pipe_steps.checkpoint.polars_step`
   - Implement `process(df: pl.DataFrame) -> pl.DataFrame`
   - Add to `pipe_steps.checkpoint.__init__.py` exports

2. **Batch Pipeline Step**:
   - Extend `BatchStep` from `pipe_steps.batch.batch_step`
   - Implement `process(batch: Batch) -> Batch`
   - Handle batch metadata (batch_id, start_row, end_row)
   - Add to `pipe_steps.batch.__init__.py` exports

3. **Path Pipeline Step**:
   - Extend `PathStep` from `pipe_steps.path.path_step`
   - Implement `process(items: list[PathItem]) -> list[PathItem]`
   - Manipulate PathItem metadata, not file contents
   - Add to `pipe_steps.path.__init__.py` exports

### Modifying Pipeline Logic

- **Checkpoint resume**: `checkpoint_pipeline.py` in `_get_resume_step()` and `run()`
- **Batch frontier tracking**: `frontier.py` for persistence, `batch_pipeline.py` for resume logic
- **Batch fetcher**: Custom function passed to `BatchPipeline` constructor

### Working with Polars

- All data operations use Polars DataFrames
- Checkpoints saved as Parquet (compressed, efficient)
- Use `pl.col()` for column expressions
- Method chaining preferred: `df.with_columns([...]).filter(...)`

## Important Notes for AI Assistants

### MANDATORY: Validation After Changes

**CRITICAL REQUIREMENT**: After completing ANY code changes, you MUST run:

```bash
make validate
```

This command runs:
- Type checking (mypy + pyright)
- Format checking (isort + black)
- Full test suite with coverage report

This is a mandatory step that must be completed before considering any task finished. Do not skip this step under any circumstances. If `make validate` fails, you must fix the issues before the task is considered complete.

### General Guidelines

1. **Do not break type safety**: All functions must have complete type hints
2. **Maintain checkpoint compatibility**: Changes to checkpoint format affect resume capability
3. **Batch coordination is critical**: All steps must process same batch before advancing
4. **PathItems are metadata only**: Path pipeline doesn't read file contents
5. **Frontier is single source of truth**: Batch pipeline uses frontier JSON to track all state
6. **Sub-package isolation**: Each pipeline type is independent, minimal cross-dependencies
7. **Abstract base classes define contracts**: Don't modify base class interfaces without updating all implementations

## File Locations Quick Reference

| What | Where |
|------|-------|
| Checkpoint pipeline orchestrator | `src/pipe_steps/checkpoint/checkpoint_pipeline.py` |
| Batch pipeline orchestrator | `src/pipe_steps/batch/batch_pipeline.py` |
| Path pipeline orchestrator | `src/pipe_steps/path/path_pipeline.py` |
| Frontier tracking logic | `src/pipe_steps/batch/frontier.py` |
| Step abstract base classes | `polars_step.py`, `batch_step.py`, `path_step.py` |
| Package-level exports | `src/pipe_steps/__init__.py` |
| Tests | `tests/unit/` |
| Configuration | `pyproject.toml` |
| Documentation | `README.md`, `README_checkpoint.md`, `README_batch.md`, `README_pipe.md` |

## Recent Changes

Based on git history:
- `5dab4f3`: FileType enum and removed itemtype
- `5ba95b9`: Added Claude prompts, reviewed with Gemini
- `33818aa`: Refactor to sub-packages, imports fixed
- `f1ccc8b`: Steps v2
- `87644f9`: Steps v1

Current branch: `steps-v6`
Main branch: `main`
