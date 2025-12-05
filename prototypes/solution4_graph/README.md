# Solution 4: Graph-Based DAG Prototype

This prototype demonstrates a **graph-based DAG** approach where steps are nodes with explicit input/output channels, and the pipeline executes them in topological order with full cycle detection and validation.

## Key Concepts

### 1. Channel-Based Steps

Steps declare explicit input and output channels:

```python
class ValidateFilesStep(PathStep):
    def get_input_channels(self) -> list[str]:
        return ["input"]

    def get_output_channels(self) -> list[str]:
        return ["valid", "invalid"]

    def process(self, inputs: dict[str, dict[str, PathItem]]) -> dict[str, dict[str, PathItem]]:
        # inputs["input"] contains PathItems
        # Returns {"valid": {...}, "invalid": {...}}
        pass
```

### 2. Explicit Connections

Channels are explicitly connected between steps:

```python
pipeline = PathPipeline()

# Add steps
pipeline.add_step("discover", DiscoverFilesStep())
pipeline.add_step("validate", ValidateFilesStep())
pipeline.add_step("process", ProcessFilesStep())

# Connect channels
pipeline.connect("discover", "validate", "output", "input")
pipeline.connect("validate", "process", "valid", "input")
```

### 3. Topological Execution

The pipeline automatically determines execution order and detects cycles:

```python
# Executes in topological order
# Validates: no cycles, all inputs connected
results = pipeline.run(initial_items)
```

## Features

### Advantages

- **Compile-time validation**: All connections validated at construction
- **Cycle detection**: Automatic detection of circular dependencies
- **Parallel execution ready**: Topological sort reveals independent branches
- **Clear structure**: DAG is explicit and visualizable
- **Type-safe connections**: Channel names must match declarations

### Limitations

- **More complex**: Requires graph concepts and explicit wiring
- **Less flexible**: Routing structure fixed at construction
- **Verbose configuration**: More code to set up pipeline
- **Steeper learning curve**: Need to understand DAG concepts

## File Structure

```
solution4_graph/
├── path_item_graph.py           # PathItem (no tags needed)
├── path_step_graph.py           # Abstract base with channel declarations
├── path_pipeline_graph.py       # DAG pipeline with topological execution
├── example_steps.py             # Example step implementations
├── demo.py                      # Demonstrations
└── README.md                    # This file
```

## Usage Example

### Basic Success/Failure DAG

```python
from pathlib import Path
from path_item_graph import PathItem
from path_pipeline_graph import PathPipeline
from example_steps import (
    DiscoverFilesStep,
    ValidateFilesStep,
    ProcessFilesStep,
    ErrorHandlerStep,
)

# Create pipeline
pipeline = PathPipeline(debug=True)

# Add steps
pipeline.add_step("discover", DiscoverFilesStep())
pipeline.add_step("validate", ValidateFilesStep())
pipeline.add_step("process", ProcessFilesStep())
pipeline.add_step("errors", ErrorHandlerStep())

# Connect channels
pipeline.connect("discover", "validate", "output", "input")
pipeline.connect("validate", "process", "valid", "input")
pipeline.connect("validate", "errors", "invalid", "input")

# Validate structure
errors = pipeline.validate()
if errors:
    for error in errors:
        print(f"Error: {error}")

# Visualize
pipeline.visualize()

# Run
initial_items = {"data_dir": PathItem(path=Path("data"))}
results = pipeline.run(initial_items)
```

### Parallel Branches with Merge

```python
# Create parallel processing branches
pipeline.add_step("discover", DiscoverFilesStep())
pipeline.add_step("filter", FilterByTypeStep())
pipeline.add_step("process_csv", ProcessFilesStep("CSV"))
pipeline.add_step("process_parquet", ProcessFilesStep("Parquet"))
pipeline.add_step("merge", MergeStep(["csv", "parquet"]))

# Split to parallel branches
pipeline.connect("discover", "filter", "output", "input")
pipeline.connect("filter", "process_csv", "csv", "input")
pipeline.connect("filter", "process_parquet", "parquet", "input")

# Merge results
pipeline.connect("process_csv", "merge", "output", "csv")
pipeline.connect("process_parquet", "merge", "output", "parquet")

# These branches can execute in parallel!
results = pipeline.run(initial_items)
```

### Custom Multi-Output Step

```python
from path_step_graph import PathStep

class SplitBySize(PathStep):
    """Split files into small/large channels."""

    def __init__(self, threshold: int):
        super().__init__("Split By Size")
        self.threshold = threshold

    def get_input_channels(self) -> list[str]:
        return ["input"]

    def get_output_channels(self) -> list[str]:
        return ["small", "large"]

    def process(self, inputs):
        small = {}
        large = {}

        for name, item in inputs["input"].items():
            if item.path.stat().st_size < self.threshold:
                small[name] = item
            else:
                large[name] = item

        return {"small": small, "large": large}
```

## Running the Demo

```bash
cd prototypes/solution4_graph
python demo.py
```

The demo includes:
1. **Basic DAG**: Success/failure branches
2. **Parallel branches**: File type routing with merge
3. **Complex DAG**: Multiple splits and merges
4. **Cycle detection**: Demonstrates validation

## DAG Validation

The pipeline provides comprehensive validation:

```python
# Validate entire pipeline structure
errors = pipeline.validate()

# Checks for:
# - Cycles in the graph
# - Disconnected input channels
# - Unused output channels
# - Multiple starting steps
# - No starting steps
```

## Visualization

```python
# Print pipeline structure
pipeline.visualize()

# Output:
# ==========================================
# PIPELINE STRUCTURE
# ==========================================
#
# Steps:
#   discover: Discover Files
#     Inputs:  ['input']
#     Outputs: ['output']
#
#   validate: Validate Files
#     Inputs:  ['input']
#     Outputs: ['valid', 'invalid']
#
# Connections:
#   discover[output] -> validate[input]
#   validate[valid] -> process[input]
#
# Execution Order:
#   1. discover
#   2. validate
#   3. process
```

## Graph Algorithms

The pipeline implements:

### Topological Sort (Kahn's Algorithm)

Determines optimal execution order:

```python
execution_order = pipeline._topological_sort()
# Returns: ['discover', 'validate', 'process', 'errors']
```

### Cycle Detection (DFS)

Detects circular dependencies:

```python
if pipeline._has_cycle():
    raise ValueError("Pipeline contains a cycle")
```

## Parallel Execution (Future)

The DAG structure enables parallel execution:

```python
# Get execution layers (steps that can run in parallel)
layers = [
    ["step1"],                    # Layer 0
    ["step2", "step3", "step4"],  # Layer 1 (parallel)
    ["step5"]                     # Layer 2
]

# Execute each layer in parallel
for layer in layers:
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(step.process, inputs) for step in layer]
        results = [f.result() for f in futures]
```

## Best Practices

1. **Validate early**: Call `pipeline.validate()` before running
2. **Visualize structure**: Use `pipeline.visualize()` for documentation
3. **Name channels clearly**: Use descriptive channel names
4. **Test connections**: Write tests that verify connections are correct
5. **Document dependencies**: Comment why steps are connected

## Connection Objects

Connections are first-class objects:

```python
@dataclass
class Connection:
    from_step: str
    to_step: str
    from_channel: str
    to_channel: str

# Access all connections
for conn in pipeline.connections:
    print(f"{conn.from_step}[{conn.from_channel}] -> {conn.to_step}[{conn.to_channel}]")
```

## Error Handling

Comprehensive error checking:

```python
# Step doesn't exist
pipeline.connect("nonexistent", "step2", "out", "in")
# ValueError: Step nonexistent not found

# Channel doesn't exist
pipeline.connect("step1", "step2", "wrong_channel", "input")
# ValueError: Step step1 does not have output channel 'wrong_channel'

# Cycle detected
pipeline.run(items)
# ValueError: Pipeline contains a cycle
```

## Comparison with Solution 2

| Feature | Solution 2 (Tags) | Solution 4 (Graph) |
|---------|-------------------|-------------------|
| Complexity | Low | High |
| Type Safety | Medium | High |
| Flexibility | High | Medium |
| Parallel execution | No | Yes |
| Compile-time validation | No | Yes |
| Dynamic routing | Excellent | Limited |

See `DAG_tradeoffs_2_vs_4.md` for detailed comparison.

## When to Use

Choose this approach when:
- ✅ You need parallel execution of independent branches
- ✅ You have complex dependency chains
- ✅ You need compile-time validation of the pipeline
- ✅ Your team is familiar with DAG frameworks (Airflow, Luigi)
- ✅ You're building a production data platform
- ✅ You want to visualize/optimize the pipeline structure

Choose Solution 2 (Tags) when:
- ✅ You need simple success/failure routing
- ✅ You want dynamic, data-driven routing
- ✅ Your team prefers simple, intuitive APIs
- ✅ You're building an MVP or prototype
- ✅ Sequential execution is sufficient
