"""Abstract base class for tag-aware path processing steps."""

from abc import ABC, abstractmethod

from .path_item_tagged import PathItem


class PathStep(ABC):
    """Abstract base class for steps that process file/directory paths with tag-based routing."""

    def __init__(self, name: str, input_tags: set[str] | None = None) -> None:
        """
        Initialize the path step.

        Args:
            name: Step name for identification
            input_tags: Set of tags this step processes. If None or empty, processes all items.
        """
        self.name = name
        self.input_tags = input_tags or set()

    @abstractmethod
    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """
        Process a dictionary of named path items and return the result.

        The items passed to this method are pre-filtered based on input_tags.
        Steps can modify tags, add/remove items, or transform the items.

        Args:
            items: Dictionary mapping names to PathItem objects that match input_tags

        Returns:
            Dictionary mapping names to PathItem objects
            (may be modified, added, removed, or have keys renamed)
        """
        pass

    def matches_item(self, item: PathItem) -> bool:
        """
        Check if this step should process the given item based on tags.

        Args:
            item: PathItem to check

        Returns:
            True if step should process this item
        """
        if not self.input_tags:
            # Empty input_tags means process everything
            return True
        return item.has_any_tag(self.input_tags)


class Tags:
    """Standard tag constants to avoid typos."""

    # Discovery tags
    DISCOVERED = "discovered"
    RAW = "raw"

    # Validation tags
    VALID = "valid"
    INVALID = "invalid"

    # Processing tags
    PROCESSED = "processed"
    TRANSFORMED = "transformed"

    # Error tags
    ERROR = "error"
    CORRUPTED = "corrupted"
    MISSING = "missing"

    # Size tags
    SMALL = "small"
    LARGE = "large"

    # Status tags
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
