"""Batch-based pipeline with frontier tracking for large datasets."""

from pathlib import Path
from typing import Callable

import polars as pl

from .batch import Batch
from .batch_step import BatchStep
from .frontier import Frontier


class BatchPipeline:
    """
    Pipeline that processes data in batches with frontier tracking.

    Supports:
    - Processing large datasets that don't fit in memory
    - Restartable pipelines that resume from frontier
    - Tracking completion state across multiple steps
    """

    def __init__(
        self,
        steps: list[BatchStep],
        batch_fetcher: Callable[[int, int], Batch | None],
        batch_size: int = 50000,
        checkpoint_dir: str = "./batch_checkpoints",
    ) -> None:
        """
        Initialize the batch pipeline.

        Args:
            steps: List of BatchStep instances to execute
            batch_fetcher: Function(batch_id, batch_size) -> Batch that fetches data
            batch_size: Number of rows per batch
            checkpoint_dir: Directory for saving checkpoints and frontier state
        """
        self.steps = steps
        self.batch_fetcher = batch_fetcher
        self.batch_size = batch_size
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True, parents=True)
        self.frontier = Frontier.load(self._get_frontier_path())

        step_names = [step.name for step in steps]
        if len(step_names) != len(set(step_names)):
            raise ValueError("Duplicate step names are not allowed in the pipeline.")

    def _get_frontier_path(self) -> Path:
        """Get path to frontier state file."""
        return self.checkpoint_dir / "frontier.json"

    def _get_batch_checkpoint_path(self, batch_id: int) -> Path:
        """Get path to save a processed batch."""
        return self.checkpoint_dir / f"batch_{batch_id}.parquet"

    def _load_batch_checkpoint(self, batch_id: int) -> pl.DataFrame | None:
        """Load a processed batch checkpoint if it exists."""
        path = self._get_batch_checkpoint_path(batch_id)
        if path.exists():
            return pl.read_parquet(path)
        return None

    def _save_batch_checkpoint(self, batch: Batch) -> None:
        """Save a processed batch to checkpoint."""
        path = self._get_batch_checkpoint_path(batch.batch_id)
        batch.data.write_parquet(path)

    def run(self, resume: bool = True) -> None:
        """
        Run the pipeline, processing batches until data is exhausted.

        Args:
            resume: If True, resume from last frontier; if False, start fresh
        """
        if not resume:
            self.frontier = Frontier()
            # Clear old checkpoints
            for path in self.checkpoint_dir.glob("batch_*.parquet"):
                path.unlink()

        batch_id = self.frontier.last_completed_batch_id + 1
        start_row = self.frontier.last_completed_row + 1

        print(f"\n{'='*60}")
        print(f"🚀 Starting batch pipeline")
        print(f"{'='*60}")
        if resume and batch_id > 0:
            print(f"📌 Resuming from frontier: batch {batch_id}, row {start_row}")

        batches_processed = 0

        while True:
            # Fetch next batch
            print(f"\n▶ Fetching batch {batch_id} (size={self.batch_size})...")
            batch = self.batch_fetcher(batch_id, self.batch_size)

            if batch is None:
                print("✓ No more data to process")
                break

            print(f"  ✓ Fetched batch {batch_id}: {batch.size} rows")

            try:
                # Process batch through all steps
                current_batch = batch
                for step in self.steps:
                    print(f"  ▶ {step.name}...", end="", flush=True)
                    current_batch = step.process(current_batch)
                    self.frontier.update_step(step.name, batch_id)
                    print(f" ({current_batch.size} rows)")

                # Save checkpoint
                self._save_batch_checkpoint(current_batch)

                # Advance frontier
                self.frontier.advance_frontier(batch_id, current_batch.end_row)
                self.frontier.save(self._get_frontier_path())

                batches_processed += 1
                print(f"  ✓ Batch {batch_id} complete: {self.frontier}")

            except Exception as e:
                print(f"\n❌ Error processing batch {batch_id}: {e}")
                print(f"📌 Frontier saved: {self.frontier}")
                raise

            batch_id += 1

        print(f"\n{'='*60}")
        print(f"✓ Pipeline complete!")
        print(f"  Batches processed: {batches_processed}")
        print(f"  Total rows: {self.frontier.total_rows_processed}")
        print(f"  {self.frontier}")
        print(f"{'='*60}\n")

    def collect_results(self) -> pl.DataFrame:
        """
        Collect all processed batches into a single DataFrame.

        Returns:
            Combined DataFrame of all processed batches
        """
        checkpoint_files = sorted(self.checkpoint_dir.glob("batch_*.parquet"))
        if not checkpoint_files:
            return pl.DataFrame()

        return pl.read_parquet(checkpoint_files)

    def get_frontier(self) -> Frontier:
        """Get current frontier state."""
        return self.frontier

    def reset_frontier(self) -> None:
        """Reset frontier to start fresh."""
        self.frontier = Frontier()
        self._get_frontier_path().unlink(missing_ok=True)
        for path in self.checkpoint_dir.glob("batch_*.parquet"):
            path.unlink()
        print("✓ Frontier reset, all checkpoints cleared")
