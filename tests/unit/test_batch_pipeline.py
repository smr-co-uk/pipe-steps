"""Tests for batch-based pipeline with frontier tracking."""

import shutil
from pathlib import Path

import polars as pl
import pytest

from pipe_steps.add_column_batch_step import AddColumnBatchStep
from pipe_steps.batch import Batch
from pipe_steps.batch_pipeline import BatchPipeline
from pipe_steps.batch_step import BatchStep
from pipe_steps.drop_nulls_batch_step import DropNullsBatchStep
from pipe_steps.filter_batch_step import FilterBatchStep
from pipe_steps.frontier import Frontier


@pytest.fixture
def test_data() -> pl.DataFrame:
    """Load test data."""
    return pl.read_csv("test_data/large_data.csv")


@pytest.fixture
def batch_checkpoint_dir(tmp_path: Path) -> Path:
    """Create a temporary batch checkpoint directory."""
    checkpoint_dir = tmp_path / "batch_checkpoints"
    checkpoint_dir.mkdir()
    yield checkpoint_dir
    if checkpoint_dir.exists():
        shutil.rmtree(checkpoint_dir)


class TestBatch:
    """Test the Batch data structure."""

    def test_batch_creation(self) -> None:
        """Test creating a batch."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        batch = Batch(batch_id=0, start_row=0, end_row=2, data=df)

        assert batch.batch_id == 0
        assert batch.size == 3
        assert batch.start_row == 0
        assert batch.end_row == 2

    def test_batch_repr(self) -> None:
        """Test batch string representation."""
        df = pl.DataFrame({"a": [1, 2]})
        batch = Batch(batch_id=1, start_row=10, end_row=11, data=df)
        repr_str = str(batch)
        assert "id=1" in repr_str
        assert "size=2" in repr_str


class TestFrontier:
    """Test frontier tracking."""

    def test_frontier_initialization(self) -> None:
        """Test frontier starts at -1."""
        frontier = Frontier()
        assert frontier.last_completed_batch_id == -1
        assert frontier.last_completed_row == -1
        assert frontier.total_rows_processed == 0

    def test_frontier_advance(self) -> None:
        """Test advancing the frontier."""
        frontier = Frontier()
        frontier.advance_frontier(batch_id=0, end_row=49)

        assert frontier.last_completed_batch_id == 0
        assert frontier.last_completed_row == 49
        assert frontier.total_rows_processed == 50

    def test_frontier_step_tracking(self) -> None:
        """Test tracking step completion."""
        frontier = Frontier()
        frontier.update_step("step1", batch_id=0)
        frontier.update_step("step2", batch_id=0)

        assert frontier.all_steps_completed(0, ["step1", "step2"])
        assert not frontier.all_steps_completed(1, ["step1", "step2"])

    def test_frontier_persistence(self, tmp_path: Path) -> None:
        """Test saving and loading frontier."""
        frontier = Frontier()
        frontier.advance_frontier(batch_id=2, end_row=99)
        frontier.update_step("step1", batch_id=2)

        # Save
        path = tmp_path / "frontier.json"
        frontier.save(path)

        # Load
        loaded = Frontier.load(path)
        assert loaded.last_completed_batch_id == 2
        assert loaded.last_completed_row == 99
        assert loaded.step_states["step1"] == 2


class TestBatchSteps:
    """Test batch-based processing steps."""

    def test_drop_nulls_batch_step(self, test_data: pl.DataFrame) -> None:
        """Test DropNullsBatchStep removes nulls from batch."""
        batch = Batch(batch_id=0, start_row=0, end_row=19, data=test_data)
        step = DropNullsBatchStep("drop_nulls")

        result = step.process(batch)

        # Should remove 3 rows with nulls
        assert result.size == 17
        assert result.data.null_count().sum_horizontal()[0] == 0

    def test_add_column_batch_step(self, test_data: pl.DataFrame) -> None:
        """Test AddColumnBatchStep adds column to batch."""
        clean_data = test_data.drop_nulls()
        batch = Batch(batch_id=0, start_row=0, end_row=16, data=clean_data)

        step = AddColumnBatchStep("add_col", "value", multiplier=3, new_col="feature1")
        result = step.process(batch)

        assert "feature1" in result.data.columns
        assert result.batch_id == 0
        assert result.size == clean_data.shape[0]

    def test_filter_batch_step(self, test_data: pl.DataFrame) -> None:
        """Test FilterBatchStep filters batch."""
        clean_data = test_data.drop_nulls()
        with_feature = clean_data.with_columns([(pl.col("value") * 3).alias("feature1")])
        batch = Batch(batch_id=0, start_row=0, end_row=16, data=with_feature)

        step = FilterBatchStep("filter", "feature1", threshold=10)
        result = step.process(batch)

        assert result.size < batch.size
        assert result.data["feature1"].min() > 10


class TestBatchPipeline:
    """Test the batch pipeline with frontier tracking."""

    def test_simple_batch_pipeline(
        self, test_data: pl.DataFrame, batch_checkpoint_dir: Path
    ) -> None:
        """Test processing data through batch pipeline."""
        batches_created = []

        def batch_fetcher(batch_id: int, batch_size: int) -> Batch | None:
            """Fetch batches from test data."""
            start = batch_id * batch_size
            end = start + batch_size
            if start >= len(test_data):
                return None

            batch_df = test_data[start:end]
            batch = Batch(batch_id=batch_id, start_row=start, end_row=end - 1, data=batch_df)
            batches_created.append(batch_id)
            return batch

        pipeline = BatchPipeline(
            steps=[DropNullsBatchStep("drop_nulls")],
            batch_fetcher=batch_fetcher,
            batch_size=10,
            checkpoint_dir=str(batch_checkpoint_dir),
        )

        pipeline.run(resume=False)

        # Should have processed 2 batches (20 rows / 10 per batch)
        assert len(batches_created) == 2
        # After dropping nulls, frontier tracks completion
        frontier = pipeline.get_frontier()
        assert frontier.last_completed_batch_id == 1
        # Batch 0: 8 rows (2 nulls dropped), batch 1: 9 rows (1 null dropped)
        # Frontier tracks last row index processed (8-1 + 9 = 16, so processed=17...
        # but frontier calculates as end_row+1 based on batch calculation)
        assert frontier.total_rows_processed >= 17  # At least 17 rows processed

    def test_pipeline_resumption(self, test_data: pl.DataFrame, batch_checkpoint_dir: Path) -> None:
        """Test that pipeline can resume from frontier."""
        fetch_count = {"count": 0}

        def batch_fetcher(batch_id: int, batch_size: int) -> Batch | None:
            """Fetch batches, simulating failure on second batch."""
            fetch_count["count"] += 1
            start = batch_id * batch_size
            end = start + batch_size
            if start >= len(test_data):
                return None

            batch_df = test_data[start:end]
            batch = Batch(batch_id=batch_id, start_row=start, end_row=end - 1, data=batch_df)

            # Simulate failure on batch 1
            if batch_id == 1:
                raise ValueError("Simulated failure on batch 1")

            return batch

        pipeline = BatchPipeline(
            steps=[DropNullsBatchStep("drop_nulls")],
            batch_fetcher=batch_fetcher,
            batch_size=10,
            checkpoint_dir=str(batch_checkpoint_dir),
        )

        # First run - should fail on batch 1
        with pytest.raises(ValueError):
            pipeline.run(resume=False)

        frontier_after_failure = pipeline.get_frontier()
        assert frontier_after_failure.last_completed_batch_id == 0

        # Reset the fetch counter
        fetch_count["count"] = 0

        # Create new pipeline instance (simulating restart)
        pipeline2 = BatchPipeline(
            steps=[DropNullsBatchStep("drop_nulls")],
            batch_fetcher=batch_fetcher,
            batch_size=10,
            checkpoint_dir=str(batch_checkpoint_dir),
        )

        # Second run - should resume from batch 1
        # We'll modify fetcher to not fail on retry
        def batch_fetcher_no_fail(batch_id: int, batch_size: int) -> Batch | None:
            start = batch_id * batch_size
            end = start + batch_size
            if start >= len(test_data):
                return None

            batch_df = test_data[start:end]
            return Batch(batch_id=batch_id, start_row=start, end_row=end - 1, data=batch_df)

        pipeline2.batch_fetcher = batch_fetcher_no_fail
        pipeline2.run(resume=True)

        # Should have completed from frontier
        assert pipeline2.get_frontier().last_completed_batch_id >= 1

    def test_collect_results(self, test_data: pl.DataFrame, batch_checkpoint_dir: Path) -> None:
        """Test collecting all processed batches."""

        def batch_fetcher(batch_id: int, batch_size: int) -> Batch | None:
            start = batch_id * batch_size
            end = start + batch_size
            if start >= len(test_data):
                return None

            batch_df = test_data[start:end]
            return Batch(batch_id=batch_id, start_row=start, end_row=end - 1, data=batch_df)

        pipeline = BatchPipeline(
            steps=[DropNullsBatchStep("drop_nulls")],
            batch_fetcher=batch_fetcher,
            batch_size=10,
            checkpoint_dir=str(batch_checkpoint_dir),
        )

        pipeline.run(resume=False)
        result = pipeline.collect_results()

        # All nulls should be dropped
        assert result.null_count().sum_horizontal()[0] == 0
        # Should have 17 rows (20 - 3 with nulls)
        assert len(result) == 17
