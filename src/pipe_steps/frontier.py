"""Frontier tracking for batch processing."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Frontier:
    """Tracks the frontier - the last row successfully processed by all steps."""

    last_completed_batch_id: int = -1
    last_completed_row: int = -1
    total_rows_processed: int = 0
    step_states: dict[str, int] = field(default_factory=lambda: {})

    def update_step(self, step_name: str, batch_id: int) -> None:
        """Update the completion state for a step."""
        self.step_states[step_name] = batch_id

    def advance_frontier(self, batch_id: int, end_row: int) -> None:
        """Advance the frontier when a batch completes all steps."""
        self.last_completed_batch_id = batch_id
        self.last_completed_row = end_row
        self.total_rows_processed = end_row + 1

    def all_steps_completed(self, batch_id: int, step_names: list[str]) -> bool:
        """Check if all steps have completed the given batch."""
        return all(self.step_states.get(step, -1) >= batch_id for step in step_names)

    def save(self, path: Path) -> None:
        """Save frontier state to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(
                {
                    "last_completed_batch_id": self.last_completed_batch_id,
                    "last_completed_row": self.last_completed_row,
                    "total_rows_processed": self.total_rows_processed,
                    "step_states": self.step_states,
                },
                f,
                indent=2,
            )

    @staticmethod
    def load(path: Path) -> "Frontier":
        """Load frontier state from JSON file."""
        if not path.exists():
            return Frontier()
        with open(path) as f:
            data: dict[str, Any] = json.load(f)
            return Frontier(
                last_completed_batch_id=data.get("last_completed_batch_id", -1),
                last_completed_row=data.get("last_completed_row", -1),
                total_rows_processed=data.get("total_rows_processed", 0),
                step_states=data.get("step_states", {}),
            )

    def __repr__(self) -> str:
        return (
            f"Frontier(batch_id={self.last_completed_batch_id}, "
            f"row={self.last_completed_row}, processed={self.total_rows_processed})"
        )
