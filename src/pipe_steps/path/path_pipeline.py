"""Pipeline for processing file/directory paths through multiple steps."""

from .path_item import PathItem
from .path_step import PathStep


class PathPipeline:
    """Pipeline that processes path items through a sequence of steps."""

    def __init__(self, steps: list[PathStep]) -> None:
        """
        Initialize the path pipeline.

        Args:
            steps: List of PathStep instances to execute
        """
        self.steps = steps

    def run(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Run the pipeline on a dictionary of named path items.

        Args:
            items: Initial dictionary mapping names to PathItem objects

        Returns:
            Processed dictionary mapping names to PathItem objects
        """
        result = items

        for step in self.steps:
            print(f"▶ {step.name}...", end="", flush=True)
            result = step.process(result)
            print(f" ({len(result)} items)")

        return result
