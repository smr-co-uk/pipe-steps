"""
Unit tests for the checkpoint pipeline
"""

import shutil
from pathlib import Path

import polars as pl
import pytest

from pipe_steps.checkpoint import (
    AddColumnStep,
    CheckpointPipeline,
    DropNullsStep,
    FilterStep,
    PolarsStep,
)


@pytest.fixture
def test_data():
    """Load the test CSV data from root repository directory"""
    return pl.read_csv("test_data/large_data.csv")


@pytest.fixture
def test_checkpoint_dir(tmp_path):
    """Create a temporary checkpoint directory"""
    checkpoint_dir = tmp_path / "test_checkpoints"
    checkpoint_dir.mkdir()
    yield str(checkpoint_dir)
    # Cleanup
    if checkpoint_dir.exists():
        shutil.rmtree(checkpoint_dir)


@pytest.fixture
def simple_pipeline(test_checkpoint_dir):
    """Create a simple test pipeline"""
    return CheckpointPipeline(
        steps=[
            DropNullsStep("drop_nulls"),
            AddColumnStep("add_feature1", "value", multiplier=3, new_col="feature1"),
        ],
        checkpoint_dir=test_checkpoint_dir,
    )


class TestPolarsSteps:
    """Test individual pipeline steps"""

    def test_drop_nulls_step(self, test_data):
        """Test that DropNullsStep removes rows with nulls"""
        step = DropNullsStep("drop_nulls")
        result = step.process(test_data)

        # Original data has 20 rows, 3 have nulls
        assert len(result) == 17
        assert result.null_count().sum_horizontal()[0] == 0

    def test_add_column_step(self, test_data):
        """Test that AddColumnStep creates correct column"""
        # First drop nulls to avoid issues
        clean_df = test_data.drop_nulls()

        step = AddColumnStep("add_col", "value", multiplier=3, new_col="feature1")
        result = step.process(clean_df)

        # Check new column exists
        assert "feature1" in result.columns

        # Check calculation is correct (value * 3)
        expected = clean_df.select((pl.col("value") * 3).alias("feature1"))
        assert result["feature1"].to_list() == expected["feature1"].to_list()

    def test_filter_step(self, test_data):
        """Test that FilterStep filters correctly"""
        # First drop nulls and add feature
        clean_df = test_data.drop_nulls()
        df_with_feature = clean_df.with_columns([(pl.col("value") * 3).alias("feature1")])

        step = FilterStep("filter", "feature1", threshold=10)
        result = step.process(df_with_feature)

        # All rows should have feature1 > 10
        assert result["feature1"].min() > 10
        # Should have filtered out some rows
        assert len(result) < len(df_with_feature)


class TestCheckpointPipeline:
    """Test the checkpoint pipeline functionality"""

    def test_pipeline_basic_execution(self, test_data, simple_pipeline):
        """Test basic pipeline execution without checkpoints"""
        result = simple_pipeline.run(test_data, resume=False)

        # Check result has expected columns
        assert "feature1" in result.columns
        # Should have dropped nulls
        assert len(result) == 17

    def test_checkpoint_creation(self, test_data, simple_pipeline):
        """Test that checkpoints are created"""
        simple_pipeline.run(test_data, resume=False)

        # Check that checkpoint files exist
        for step in simple_pipeline.steps:
            checkpoint_path = simple_pipeline._get_checkpoint_path(step.name)
            assert checkpoint_path.exists()

    def test_checkpoint_resume(self, test_data, simple_pipeline):
        """Test resuming from checkpoint"""
        # First run - creates checkpoints
        result1 = simple_pipeline.run(test_data, resume=False)

        # Second run - should resume from checkpoint
        result2 = simple_pipeline.run(test_data, resume=True)

        # Results should be identical
        assert result1.equals(result2)

    def test_clear_checkpoints(self, test_data, simple_pipeline):
        """Test clearing checkpoints"""
        # Create checkpoints
        simple_pipeline.run(test_data, resume=False)

        # Clear all checkpoints
        simple_pipeline.clear_checkpoints()

        # Check that no checkpoint files exist
        for step in simple_pipeline.steps:
            checkpoint_path = simple_pipeline._get_checkpoint_path(step.name)
            assert not checkpoint_path.exists()

    def test_clear_specific_checkpoint(self, test_data, simple_pipeline):
        """Test clearing a specific checkpoint"""
        # Create checkpoints
        simple_pipeline.run(test_data, resume=False)

        # Clear only the first checkpoint
        simple_pipeline.clear_checkpoints("drop_nulls")

        # Check that only drop_nulls is cleared
        assert not simple_pipeline._get_checkpoint_path("drop_nulls").exists()
        assert simple_pipeline._get_checkpoint_path("add_feature1").exists()

    def test_clear_from_step(self, test_data, test_checkpoint_dir):
        """Test clearing checkpoints from a specific step onwards"""
        pipeline = CheckpointPipeline(
            steps=[
                DropNullsStep("drop_nulls"),
                AddColumnStep("add_feature1", "value", multiplier=3, new_col="feature1"),
                AddColumnStep("add_feature2", "feature1", multiplier=2, new_col="feature2"),
            ],
            checkpoint_dir=test_checkpoint_dir,
        )

        # Create checkpoints
        pipeline.run(test_data, resume=False)

        # Clear from add_feature1 onwards
        pipeline.clear_from("add_feature1")

        # Check that drop_nulls still exists, but others don't
        assert pipeline._get_checkpoint_path("drop_nulls").exists()
        assert not pipeline._get_checkpoint_path("add_feature1").exists()
        assert not pipeline._get_checkpoint_path("add_feature2").exists()


class TestIntegration:
    """Integration tests with the full pipeline"""

    def test_full_pipeline(self, test_data, test_checkpoint_dir):
        """Test the complete pipeline with all steps"""
        pipeline = CheckpointPipeline(
            steps=[
                DropNullsStep("drop_nulls"),
                AddColumnStep("add_feature1", "value", multiplier=3, new_col="feature1"),
                AddColumnStep("add_feature2", "feature1", multiplier=2, new_col="feature2"),
                FilterStep("filter_data", "feature1", threshold=10),
            ],
            checkpoint_dir=test_checkpoint_dir,
        )

        result = pipeline.run(test_data, resume=False)

        # Check final result has all expected columns
        expected_cols = ["id", "category", "value", "status", "feature1", "feature2"]
        assert all(col in result.columns for col in expected_cols)

        # Check data transformations
        # Original: 20 rows, drop 3 nulls = 17, filter removes 1 (value=3*3=9<=10) = 16
        assert len(result) == 16

        # All feature1 values should be > 10
        assert result["feature1"].min() > 10

        # feature2 should be 2 * feature1
        assert (result["feature2"] == result["feature1"] * 2).all()

    def test_partial_resume(self, test_data, test_checkpoint_dir):
        """Test resuming from a partial checkpoint"""
        pipeline = CheckpointPipeline(
            steps=[
                DropNullsStep("drop_nulls"),
                AddColumnStep("add_feature1", "value", multiplier=3, new_col="feature1"),
                AddColumnStep("add_feature2", "feature1", multiplier=2, new_col="feature2"),
            ],
            checkpoint_dir=test_checkpoint_dir,
        )

        # First run
        result1 = pipeline.run(test_data, resume=False)

        # Clear the last checkpoint
        pipeline.clear_from("add_feature2")

        # Run again - should resume from add_feature1
        result2 = pipeline.run(test_data, resume=True)

        # Results should be identical
        assert result1.equals(result2)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_pipeline(self, test_data, test_checkpoint_dir):
        """Test pipeline with no steps"""
        pipeline = CheckpointPipeline(steps=[], checkpoint_dir=test_checkpoint_dir)
        result = pipeline.run(test_data, resume=False)

        # Should return the original dataframe unchanged
        assert result.equals(test_data)

    def test_step_name_uniqueness(self, test_checkpoint_dir):
        """Test that creating a pipeline with duplicate step names raises an error"""
        with pytest.raises(ValueError, match="Duplicate step names are not allowed in the pipeline."):
            CheckpointPipeline(
                steps=[
                    DropNullsStep("duplicate_name"),
                    AddColumnStep("duplicate_name", "value", multiplier=2),
                ],
                checkpoint_dir=test_checkpoint_dir,
            )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
