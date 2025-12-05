# Solution 2: Tag-Based Routing Prototype

This prototype demonstrates a **tag-based routing** approach for the PathPipeline where items carry tags and steps subscribe to specific tags for automatic routing.

## Key Concepts

### 1. Tagged PathItems

Items carry a set of string tags that determine which steps process them:

```python
@dataclass
class PathItem:
    path: Path
    file_type: FileType | None = None
    tags: set[str] = field(default_factory=set)
    tag_history: list[tuple[str, str]] = field(default_factory=list)
```

### 2. Tag-Aware Steps

Steps declare which tags they process via `input_tags`:

```python
class ValidateFilesStep(PathStep):
    def __init__(self):
        super().__init__("validate_files", input_tags={"discovered"})

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        # Only processes items tagged with "discovered"
        # Can add new tags like "valid" or "invalid"
        pass
```

### 3. Automatic Routing

The pipeline automatically routes items to steps based on tag matching:

```python
pipeline = PathPipeline([
    DiscoverFilesStep(),        # Adds "discovered" tag
    ValidateFilesStep(),        # Processes "discovered", adds "valid"/"invalid"
    ProcessValidFilesStep(),    # Processes "valid"
    ErrorHandlerStep(),         # Processes "invalid"
])
```

## Features

### Advantages

- **Simple API**: Just add/remove tags, no explicit routing configuration
- **Flexible routing**: Runtime decisions based on data
- **Easy debugging**: Linear execution, easy to trace
- **Success/failure handling**: Natural branching with tags
- **Tag history**: Track which step added which tag

### Limitations

- **No parallel execution**: Steps run sequentially
- **No compile-time validation**: Tag typos caught at runtime
- **Hard to visualize**: Routing structure not explicit upfront

## File Structure

```
solution2_tags/
├── path_item_tagged.py          # PathItem with tags and history
├── path_step_tagged.py          # Abstract base with input_tags
├── path_pipeline_tagged.py      # Pipeline with tag-based routing
├── example_steps.py             # Example step implementations
├── demo.py                      # Demonstrations
└── README.md                    # This file
```

## Usage Example

### Basic Success/Failure Routing

```python
from pathlib import Path
from path_item_tagged import PathItem
from path_pipeline_tagged import PathPipeline
from example_steps import (
    DiscoverFilesStep,
    ValidateFilesStep,
    ProcessValidFilesStep,
    ErrorHandlerStep,
)

# Create pipeline
pipeline = PathPipeline([
    DiscoverFilesStep(recursive=True),
    ValidateFilesStep(min_size=10),
    ProcessValidFilesStep(),
    ErrorHandlerStep(),
], debug=True)

# Run
initial_items = {"data_dir": PathItem(path=Path("data"))}
results = pipeline.run(initial_items)

# Inspect results
for name, item in results.items():
    print(f"{name}: {item.tags}")
    print(f"  History: {item.tag_history}")
```

### Custom Step with Dynamic Routing

```python
from path_step_tagged import PathStep, Tags

class SizeClassifierStep(PathStep):
    """Classify files by size."""

    def __init__(self):
        super().__init__("size_classifier", input_tags={Tags.DISCOVERED})

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        for name, item in items.items():
            if item.is_file():
                size = item.path.stat().st_size

                # Dynamic routing based on size
                if size < 1024:
                    item.add_tag("tiny", self.name)
                elif size < 1024 * 1024:
                    item.add_tag("small", self.name)
                else:
                    item.add_tag("large", self.name)

        return items
```

## Standard Tags

The `Tags` class provides constants to avoid typos:

```python
from path_step_tagged import Tags

# Discovery
Tags.DISCOVERED
Tags.RAW

# Validation
Tags.VALID
Tags.INVALID

# Processing
Tags.PROCESSED
Tags.TRANSFORMED

# Errors
Tags.ERROR
Tags.CORRUPTED
Tags.MISSING

# Size
Tags.SMALL
Tags.LARGE

# Status
Tags.SUCCESS
Tags.FAILURE
Tags.RETRY
```

## Running the Demo

```bash
cd prototypes/solution2_tags
python demo.py
```

The demo includes:
1. **Basic routing**: Success/failure branches
2. **Parallel branches**: File type routing (CSV/Parquet)
3. **Dynamic routing**: Size-based classification

## Tag History Tracking

Each PathItem maintains a history of tag changes:

```python
item.add_tag("valid", step_name="validate")
item.remove_tag("discovered", step_name="validate")

# View history
print(item.tag_history)
# [('validate', 'valid'), ('validate', '-discovered')]
```

## Best Practices

1. **Use tag constants**: Prefer `Tags.VALID` over `"valid"` to avoid typos
2. **Remove processed tags**: Clean up tags after processing to avoid confusion
3. **Document tag flow**: Comment which tags each step expects/produces
4. **Keep tag names simple**: Use short, descriptive names
5. **Validate in tests**: Check that steps produce expected tags

## Validation

The pipeline provides validation helpers:

```python
# Check for issues
warnings = pipeline.validate()
for warning in warnings:
    print(warning)

# Visualize routing structure
pipeline.visualize_routing()
```

## Comparison with Solution 4

| Feature | Solution 2 (Tags) | Solution 4 (Graph) |
|---------|-------------------|-------------------|
| Complexity | Low | High |
| Flexibility | High | Medium |
| Parallel execution | No | Yes |
| Compile-time safety | No | Yes |
| Dynamic routing | Excellent | Limited |

See `DAG_tradeoffs_2_vs_4.md` for detailed comparison.
