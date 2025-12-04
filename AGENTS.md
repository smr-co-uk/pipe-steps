# Repository Guidelines

## Project Structure & Module Organization
- Source in `src/pipe_steps/`: `checkpoint`, `batch`, and `path` subpackages with `main_*` demo entrypoints and step classes; shared exports in `src/pipe_steps/__init__.py`.
- Tests in `tests/unit/` mirroring the package layout; fixtures/data in `test_files/` and `test_data/`.
- Docs and walkthroughs: `README.md` (overview) plus pipeline-specific guides (`README_checkpoint.md`, `README_batch.md`, `README_pipe.md`); change log in `CHANGES.md`.

## Build, Test, and Development Commands
- Install locally (Python 3.12+): `uv pip install -e .`.
- Run suite: `make test` or `uv run pytest -v --cov=pipe_steps`; generate HTML coverage with `make coverage` (see `htmlcov/index.html`).
- Quality gates: `make typecheck` (`mypy` + `pyright`), `make format` (`isort` + `black`), `make lint` (types + format check), `make check` (lint + tests), `make validate` (full QA). Build distributions with `uv build`.
- Demos: `python -m pipe_steps.checkpoint.main_checkpoint`, `python -m pipe_steps.batch.main_batch`, `python -m pipe_steps.path.main_pipe`.

## Coding Style & Naming Conventions
- Python 3.12, Polars-first. Favor pure, side-effect-light steps that return new DataFrames/Batches.
- Formatting: `black` + `isort` with 100-char lines; keep imports sorted.
- Typing: strict (`disallow_untyped_defs`, `pyright` strict). Annotate new functions/classes; prefer `pathlib.Path`, `pl.DataFrame`, and typed dataclasses as in existing steps.
- Naming: modules `snake_case`, classes `PascalCase` (e.g., `DropNullsBatchStep`), functions/vars `snake_case`; step identifiers should be short and descriptive (e.g., `"filter_nulls"`).

## Testing Guidelines
- Place unit tests alongside pipeline area (e.g., `tests/unit/batch/test_batch_pipeline.py`).
- Name files/functions `test_*`; organize by behavior (resume, frontier, filtering) rather than implementation internals.
- Cover new steps plus resume/restart paths; refresh coverage with `make coverage`. Targeted runs: `uv run pytest tests/unit/path/test_path_pipeline.py -k scenario`.

## Commit & Pull Request Guidelines
- Commit style matches history: short imperative summary with optional scope and PR/issue tag, e.g., `Add frontier reset (#12)`.
- PRs: describe what/why, pipeline touched (batch/checkpoint/path), test commands executed, and any data assumptions; include screenshots or logs for coverage/demos when relevant.
