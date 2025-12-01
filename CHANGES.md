# Changes

## 0.1.1 (2025-12-01)

### Fixed

*   **Duplicate Step Names:** Implemented a check in both `CheckpointPipeline` and `BatchPipeline` to prevent the creation of pipelines with duplicate step names. Attempting to create a pipeline with non-unique step names will now raise a `ValueError`. This addresses a potential defect where duplicate step names could lead to overwritten checkpoints or incorrect state tracking.

### Changed

*   **BatchPipeline `collect_results` Performance:** Optimized the `collect_results` method in `BatchPipeline` to use `polars.read_parquet` with a glob pattern. This change significantly improves performance when collecting results from a large number of batch checkpoint files by leveraging Polars' optimized multi-file reading capabilities.
