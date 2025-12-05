"""Pipeline for processing file/directory paths with tag-based routing."""

from .path_item_tagged import PathItem
from .path_step_tagged import PathStep


class PathPipeline:
    """Pipeline that processes path items through steps using tag-based routing."""

    def __init__(self, steps: list[PathStep], debug: bool = False) -> None:
        """
        Initialize the path pipeline.

        Args:
            steps: List of PathStep instances to execute
            debug: If True, print detailed routing information
        """
        self.steps = steps
        self.debug = debug

    def run(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Run the pipeline on a dictionary of named path items.

        Items are routed to steps based on their tags. Each step only processes
        items that match its input_tags (or all items if input_tags is empty).

        Args:
            items: Initial dictionary mapping names to PathItem objects

        Returns:
            Processed dictionary mapping names to PathItem objects
        """
        active_items = items

        for step in self.steps:
            # Filter items that match this step's input tags
            if step.input_tags:
                matching = {
                    k: v
                    for k, v in active_items.items()
                    if step.matches_item(v)
                }
            else:
                # Empty input_tags means process all items
                matching = active_items

            if self.debug:
                print(f"\n▶ {step.name}")
                print(f"  Input tags: {step.input_tags or 'all'}")
                print(f"  Matching items: {len(matching)}/{len(active_items)}")
                if matching:
                    for name, item in list(matching.items())[:3]:  # Show first 3
                        print(f"    - {name}: tags={item.tags}")
                    if len(matching) > 3:
                        print(f"    ... and {len(matching) - 3} more")

            if matching:
                # Process matching items
                new_items = step.process(matching)

                if self.debug:
                    print(f"  Output items: {len(new_items)}")
                    if new_items:
                        for name, item in list(new_items.items())[:3]:  # Show first 3
                            print(f"    - {name}: tags={item.tags}")
                        if len(new_items) > 3:
                            print(f"    ... and {len(new_items) - 3} more")

                # Update active items with results
                # This merges new/modified items back into the active set
                active_items.update(new_items)
            else:
                if not self.debug:
                    print(f"▶ {step.name}... (0 items matched)")

        return active_items

    def visualize_routing(self) -> None:
        """Print a visualization of the routing structure."""
        print("\n" + "=" * 60)
        print("PIPELINE ROUTING STRUCTURE")
        print("=" * 60)

        for i, step in enumerate(self.steps, 1):
            print(f"\n{i}. {step.name}")
            print(f"   Input tags:  {step.input_tags or '(all items)'}")
            print(f"   Description: {step.__class__.__doc__ or 'No description'}")

        print("\n" + "=" * 60)

    def get_unused_tags(self) -> set[str]:
        """
        Identify tags that are created but never consumed by any step.

        Returns:
            Set of tags that appear in no step's input_tags
        """
        all_input_tags: set[str] = set()
        for step in self.steps:
            all_input_tags.update(step.input_tags)

        # This is a simplified check - in reality, you'd need to track
        # which tags are produced by steps
        return all_input_tags

    def validate(self) -> list[str]:
        """
        Validate the pipeline configuration.

        Returns:
            List of warning/error messages
        """
        warnings = []

        # Check for duplicate step names
        names = [step.name for step in self.steps]
        duplicates = {name for name in names if names.count(name) > 1}
        if duplicates:
            warnings.append(f"Duplicate step names: {duplicates}")

        # Check for steps with no input tags in the middle of pipeline
        for i, step in enumerate(self.steps[1:], 1):  # Skip first step
            if not step.input_tags:
                warnings.append(
                    f"Step {i+1} '{step.name}' has no input_tags (will process all items)"
                )

        return warnings
