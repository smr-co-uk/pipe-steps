"""
Checkpoint Pipeline for Polars DataFrames

A pipeline system that saves intermediate results as parquet files,
allowing for resume-from-checkpoint functionality.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import polars as pl

from .polars_step import PolarsStep


class CheckpointPipeline:
    """
    Pipeline that executes steps sequentially with checkpoint saving.

    Supports:
    - Automatic checkpoint saving after each step
    - Resume from last successful checkpoint
    - Clear specific or all checkpoints
    """

    def __init__(self, steps: list[PolarsStep], checkpoint_dir: str = "./checkpoints"):
        self.steps = steps
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True, parents=True)

    def _get_checkpoint_path(self, step_name: str) -> Path:
        """Get the path for a checkpoint file"""
        return self.checkpoint_dir / f"{step_name}.parquet"

    def _load_checkpoint(self, step_name: str) -> Optional[pl.DataFrame]:
        """Load a checkpoint if it exists"""
        path = self._get_checkpoint_path(step_name)
        if path.exists():
            print(f"✓ Loading checkpoint: {step_name}")
            return pl.read_parquet(path)
        return None

    def _save_checkpoint(self, df: pl.DataFrame, step_name: str) -> None:
        """Save a checkpoint"""
        path = self._get_checkpoint_path(step_name)
        print(f"💾 Saving checkpoint: {step_name}")
        df.write_parquet(path)

    def run(self, initial_df: pl.DataFrame, resume: bool = True) -> pl.DataFrame:
        """
        Run the pipeline with automatic checkpointing and resume capability.

        Args:
            initial_df: Starting DataFrame
            resume: If True, resume from last successful checkpoint

        Returns:
            Final processed DataFrame
        """
        df = initial_df
        start_idx = 0

        if resume:
            # Find the last completed checkpoint
            for i in range(len(self.steps) - 1, -1, -1):
                step_name = self.steps[i].name
                checkpoint_df = self._load_checkpoint(step_name)
                if checkpoint_df is not None:
                    print(f"🔄 Resuming from checkpoint: {step_name}")
                    df = checkpoint_df
                    start_idx = i + 1
                    break

        # Run remaining steps
        for step in self.steps[start_idx:]:
            print(f"▶ Running step: {step.name} at {datetime.now().strftime('%H:%M:%S')}")
            df = step.process(df)
            self._save_checkpoint(df, step.name)
            print(f"  ✓ Completed: {step.name} ({len(df)} rows)")

        return df

    def list_checkpoints(self) -> None:
        """Show which checkpoints exist"""
        print("\n📋 Checkpoint status:")
        for step in self.steps:
            exists = "✓" if self._get_checkpoint_path(step.name).exists() else "✗"
            size = ""
            if exists == "✓":
                size_bytes = self._get_checkpoint_path(step.name).stat().st_size
                size = f" ({size_bytes / 1024:.1f} KB)"
            print(f"  {exists} {step.name}{size}")

    def clear_checkpoints(self, step_name: Optional[str] = None) -> None:
        """
        Clear checkpoints for a specific step or all steps

        Args:
            step_name: Name of step to clear, or None to clear all
        """
        if step_name:
            path = self._get_checkpoint_path(step_name)
            if path.exists():
                path.unlink()
                print(f"🗑️  Cleared checkpoint: {step_name}")
        else:
            for step in self.steps:
                path = self._get_checkpoint_path(step.name)
                if path.exists():
                    path.unlink()
            print("🗑️  Cleared all checkpoints")

    def clear_from(self, step_name: str) -> None:
        """
        Clear checkpoints from a specific step onwards

        Args:
            step_name: Name of step to start clearing from
        """
        found = False
        for step in self.steps:
            if step.name == step_name:
                found = True
            if found:
                path = self._get_checkpoint_path(step.name)
                if path.exists():
                    path.unlink()
                    print(f"🗑️  Cleared: {step.name}")
