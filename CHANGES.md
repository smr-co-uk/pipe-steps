# Changes

## 0.1.0 (2025-12-01)

### Added

*   **Sub-Package Organization:** Reorganized all three pipeline types into dedicated sub-packages for better code organization and maintainability:
    - `pipe_steps.checkpoint` - Checkpoint-based pipeline
    - `pipe_steps.batch` - Batch-based pipeline with frontier tracking
    - `pipe_steps.path` - Path processing pipeline
    All classes are re-exported from main `pipe_steps` package for backward compatibility.

*   **`make validate` Target:** New comprehensive quality assurance target that runs type checking, format checking, tests, and coverage analysis in one command. Useful for pre-commit validation and CI/CD pipelines.

*   **Git Pre-Commit Hook:** Added `.githooks/pre-commit` hook that automatically runs `make validate` before commits, ensuring code quality standards are maintained. Users can enable with `git config core.hooksPath .githooks`.

### Changed

*   **File Naming:** Renamed `main.py` to `main_checkpoint.py` for consistency with other pipeline demo scripts (`main_batch.py`, `main_pipe.py`).

*   **Test Organization:** Reorganized tests to mirror source code structure:
    - `tests/unit/checkpoint/` - Checkpoint pipeline tests
    - `tests/unit/batch/` - Batch pipeline tests
    - `tests/unit/path/` - Path pipeline tests

*   **Main README:** Completely restructured `README.md` to provide:
    - Overview comparing all three pipeline types

*   **CLI Script References:** Updated all `pyproject.toml` CLI scripts to reference new sub-package locations:
    - `checkpoint-pipeline` → `pipe_steps.checkpoint.main_checkpoint:main`
    - `batch-pipeline` → `pipe_steps.batch.main_batch:main`
    - `path-pipeline` → `pipe_steps.path.main_pipe:main`
---

## 0.1.1 (2025-12-01)

### Fixed

*   **Duplicate Step Names:** Implemented a check in both `CheckpointPipeline` and `BatchPipeline` to prevent the creation of pipelines with duplicate step names. Attempting to create a pipeline with non-unique step names will now raise a `ValueError`. This addresses a potential defect where duplicate step names could lead to overwritten checkpoints or incorrect state tracking.

### Changed

*   **BatchPipeline `collect_results` Performance:** Optimized the `collect_results` method in `BatchPipeline` to use `polars.read_parquet` with a glob pattern. This change significantly improves performance when collecting results from a large number of batch checkpoint files by leveraging Polars' optimized multi-file reading capabilities.
