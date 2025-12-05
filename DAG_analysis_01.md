# DAG-Based Routing Analysis for PathPipeline

## Requirements Summary

From `DAG.md`:
- Add branching/routing to PathPipeline so PathItems can be routed to specific PathSteps
- Handle failures by routing to different PathSteps
- PathStep signature: `process(self, items: dict[str, PathItem]) -> dict[str, PathItem]`
- Steps pick items by name from input dict and return named outputs
- Pipeline should know which named items each step requires and produces
- Goal: Create a DAG structure for routing

## Current Architecture

**PathStep** (already using dict-based interface):
```python
class PathStep(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """Process named path items and return results"""
        pass
```

**PathPipeline** (currently linear):
```python
class PathPipeline:
    def __init__(self, steps: list[PathStep]) -> None:
        self.steps = steps

    def run(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        result = items
        for step in self.steps:  # Linear execution
            result = step.process(result)
        return result
```

**PathItem** (metadata only):
```python
@dataclass
class PathItem:
    path: Path
    file_type: FileType | None = None
```

---

## Solution 1: Declarative Port-Based DAG

Steps declare input/output "ports" (named channels), and the pipeline builds a DAG.

### Design

```python
class PathStep(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_input_ports(self) -> list[str]:
        """Declare which named inputs this step consumes"""
        pass

    @abstractmethod
    def get_output_ports(self) -> list[str]:
        """Declare which named outputs this step produces"""
        pass

    @abstractmethod
    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """Process only the items from declared input ports"""
        pass

class ValidateFilesStep(PathStep):
    def get_input_ports(self) -> list[str]:
        return ["discovered"]

    def get_output_ports(self) -> list[str]:
        return ["valid", "invalid"]

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        result = {}
        for name, item in items.items():
            if self._is_valid(item):
                result["valid"] = item
            else:
                result["invalid"] = item
        return result
```

### Pipeline Configuration

```python
class PathPipeline:
    def __init__(self, steps: list[PathStep], edges: list[tuple[str, str]]):
        """
        Args:
            steps: List of PathStep instances
            edges: Connections like [("step1.valid", "step2.input"),
                                    ("step1.invalid", "error_handler.input")]
        """
        self.dag = self._build_dag(steps, edges)

    def _build_dag(self, steps, edges):
        # Validate all connections exist
        # Detect cycles
        # Build execution graph
        pass
```

### Pros
- Explicit, type-safe declarations
- Can validate DAG at construction (detect cycles, missing connections)
- Clear visualization of data flow
- Can optimize execution order
- Compile-time safety

### Cons
- More verbose step definitions (need to declare ports)
- Requires explicit wiring configuration
- Less flexible for dynamic routing
- Higher upfront complexity

### Use Cases
- Complex multi-branch workflows
- When you need to validate the entire flow before execution
- When visualization/documentation of flow is important
- Production systems requiring safety guarantees

---

## Solution 2: Tag-Based Routing

PathItems carry tags, steps subscribe to tags, pipeline routes automatically.

### Design

```python
@dataclass
class PathItem:
    path: Path
    file_type: FileType | None = None
    tags: set[str] = field(default_factory=set)  # NEW

class PathStep(ABC):
    def __init__(self, name: str, input_tags: set[str]):
        self.name = name
        self.input_tags = input_tags  # Which tags this step processes

    @abstractmethod
    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        """Items are pre-filtered by tags, outputs can have new tags"""
        pass

class ValidateFilesStep(PathStep):
    def __init__(self):
        super().__init__("validate", input_tags={"discovered"})

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        result = {}
        for name, item in items.items():
            if self._is_valid(item):
                item.tags.add("valid")
                result[name] = item
            else:
                item.tags.add("invalid")
                result[name] = item
        return result

class ErrorHandlerStep(PathStep):
    def __init__(self):
        super().__init__("error_handler", input_tags={"invalid"})

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        # Only processes items tagged "invalid"
        return self._handle_errors(items)
```

### Pipeline Execution

```python
class PathPipeline:
    def __init__(self, steps: list[PathStep]):
        self.steps = steps

    def run(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        # Automatically routes items to steps based on tags
        active_items = items

        for step in self.steps:
            # Filter items matching this step's input tags
            matching = {
                k: v for k, v in active_items.items()
                if step.input_tags & v.tags
            }

            if matching:
                new_items = step.process(matching)
                active_items.update(new_items)

        return active_items
```

### Pros
- Flexible, data-driven routing
- Easy to add new routing paths
- Items self-describe their state
- Simple step definitions
- Minimal API changes to existing code
- Natural extension of existing file_type concept
- Can handle dynamic routing at runtime

### Cons
- Harder to visualize complete data flow upfront
- No compile-time validation of routes
- Potential for tag conflicts/ambiguity
- May be unclear which steps process which items
- Debugging can be harder (which step added which tag?)

### Use Cases
- Success/failure routing
- Multi-stage filtering/classification
- Dynamic workflows where routing depends on runtime conditions
- Incremental migration from existing linear pipelines

---

## Solution 3: Explicit Channel Routing

Steps route outputs to named channels, pipeline manages channel state.

### Design

```python
@dataclass
class StepOutput:
    items: dict[str, PathItem]
    target_channel: str  # Where these items go next

class PathStep(ABC):
    @abstractmethod
    def process(self, items: dict[str, PathItem]) -> list[StepOutput]:
        """Can return multiple outputs to different channels"""
        pass

class ValidateFilesStep(PathStep):
    def process(self, items: dict[str, PathItem]) -> list[StepOutput]:
        valid = {}
        invalid = {}

        for name, item in items.items():
            if self._is_valid(item):
                valid[name] = item
            else:
                invalid[name] = item

        return [
            StepOutput(valid, target_channel="valid"),
            StepOutput(invalid, target_channel="error")
        ]
```

### Pipeline Configuration

```python
class PathPipeline:
    def __init__(self, routing_map: dict[str, PathStep]):
        """
        Args:
            routing_map: Maps channel names to steps
                        {"valid": ProcessValidStep(),
                         "error": ErrorHandlerStep()}
        """
        self.routing_map = routing_map

    def run(self, initial_items: dict[str, PathItem]) -> dict[str, PathItem]:
        channels: dict[str, dict[str, PathItem]] = {"input": initial_items}

        # Process each channel
        for channel_name, target_step in self.routing_map.items():
            if channel_name in channels:
                outputs = target_step.process(channels[channel_name])
                for output in outputs:
                    channels[output.target_channel] = output.items

        return channels
```

### Pros
- Explicit control over routing decisions
- Easy to understand step-by-step execution
- Can handle multiple outputs cleanly
- Flexible routing at runtime
- Clear separation between step logic and routing

### Cons
- Manual routing configuration
- Not truly a DAG (more of a workflow engine)
- Can't easily optimize execution order
- Requires understanding channel names across steps
- Order of routing_map matters

### Use Cases
- Sequential workflows with branching
- ETL pipelines with error handling
- Simple success/failure splits
- When you want explicit control over execution order

---

## Solution 4: Graph-Based Pipeline (Full DAG)

True DAG with steps as nodes, explicit edges, topological execution.

### Design

```python
from typing import Protocol

class PathPipeline:
    def __init__(self):
        self.graph: dict[str, list[str]] = {}  # step_id -> [dependent_step_ids]
        self.steps: dict[str, PathStep] = {}
        self.channels: dict[tuple[str, str], tuple[str, str]] = {}
        # (from_step, to_step) -> (from_channel, to_channel)

    def add_step(self, step_id: str, step: PathStep) -> None:
        """Add a step to the DAG"""
        self.steps[step_id] = step
        self.graph[step_id] = []

    def connect(self, from_step: str, to_step: str,
                from_channel: str, to_channel: str) -> None:
        """Connect output channel of one step to input channel of another"""
        if from_step not in self.graph:
            raise ValueError(f"Step {from_step} not found")
        if to_step not in self.graph:
            raise ValueError(f"Step {to_step} not found")

        self.graph[from_step].append(to_step)
        self.channels[(from_step, to_step)] = (from_channel, to_channel)

    def _topological_sort(self) -> list[str]:
        """Return steps in execution order, detecting cycles"""
        # Kahn's algorithm or DFS-based topological sort
        pass

    def _gather_inputs(self, step_id: str,
                       step_outputs: dict[str, dict[str, dict[str, PathItem]]]) -> dict[str, PathItem]:
        """Gather inputs for a step from its predecessors"""
        inputs = {}
        for pred_step in self.graph:
            if step_id in self.graph[pred_step]:
                from_ch, to_ch = self.channels[(pred_step, step_id)]
                if pred_step in step_outputs and from_ch in step_outputs[pred_step]:
                    inputs[to_ch] = step_outputs[pred_step][from_ch]
        return inputs

    def run(self, initial_items: dict[str, PathItem]) -> dict[str, PathItem]:
        """Execute the DAG in topological order"""
        # Validate DAG (no cycles)
        if self._has_cycle():
            raise ValueError("DAG contains cycles")

        # Topological sort to determine execution order
        execution_order = self._topological_sort()

        # Track outputs at each step
        step_outputs: dict[str, dict[str, dict[str, PathItem]]] = {}

        for step_id in execution_order:
            # Gather inputs from connected predecessor steps
            inputs = self._gather_inputs(step_id, step_outputs)

            # Execute step
            outputs = self.steps[step_id].process(inputs)
            step_outputs[step_id] = outputs

        # Return outputs from final step(s)
        return step_outputs[execution_order[-1]]
```

### Usage Example

```python
pipeline = PathPipeline()

# Add steps
pipeline.add_step("discover", DiscoverFilesStep())
pipeline.add_step("validate", ValidateFilesStep())
pipeline.add_step("process_valid", ProcessValidStep())
pipeline.add_step("handle_errors", ErrorHandlerStep())

# Connect them
pipeline.connect("discover", "validate", "all", "input")
pipeline.connect("validate", "process_valid", "valid", "input")
pipeline.connect("validate", "handle_errors", "invalid", "input")

# Run
results = pipeline.run({"start": PathItem(Path("data/"))})
```

### Pros
- True DAG structure with full graph semantics
- Can detect cycles, validate correctness
- Can optimize execution order
- Supports parallel execution of independent branches
- Most powerful and flexible
- Can visualize with graph tools

### Cons
- Most complex to implement
- Requires graph algorithms (topological sort, cycle detection)
- Higher learning curve for users
- May be overkill for simple pipelines
- More verbose configuration

### Use Cases
- Complex multi-branch workflows
- When branches can run in parallel
- When you need cycle detection
- Large production systems
- When you want to visualize/optimize the pipeline

---

## Comparison Matrix

| Feature | Port-Based | Tag-Based | Channel | Graph |
|---------|-----------|-----------|---------|-------|
| **Complexity** | Medium | Low | Low | High |
| **Type Safety** | High | Medium | Medium | High |
| **Flexibility** | Medium | High | Medium | Very High |
| **Validation** | Compile-time | Runtime | Runtime | Construction-time |
| **Visualization** | Easy | Hard | Medium | Easy |
| **Learning Curve** | Medium | Low | Low | High |
| **Parallel Execution** | Possible | No | No | Yes |
| **Dynamic Routing** | No | Yes | Yes | No |
| **API Changes** | Moderate | Minimal | Moderate | Significant |

---

## Recommendation

**Start with Solution 2 (Tag-Based Routing)** because:

1. **Minimal API changes** - Just add `tags: set[str]` to PathItem
2. **Incremental adoption** - Works alongside existing linear pipelines
3. **Natural fit** - Files already have `file_type`, tags are a natural extension
4. **Handles success/failure elegantly** - Add "valid"/"invalid" tags
5. **Simple to understand** - Tags are intuitive
6. **Low risk** - Easy to implement and test

### Evolution Path

1. **Phase 1**: Implement tag-based routing (Solution 2)
2. **Phase 2**: Add optional port declarations for documentation (hybrid approach)
3. **Phase 3**: If needed, evolve to full DAG (Solution 4) for:
   - Parallel execution
   - Complex dependency graphs
   - Automatic optimization

### Why Not the Others Initially?

- **Solution 1 (Port-Based)**: More upfront work, requires rethinking all steps
- **Solution 3 (Channel)**: Not much simpler than tags, less flexible
- **Solution 4 (Graph)**: Overkill unless you need parallel execution or complex routing

---

## Implementation Sketch for Tag-Based Approach

### Step 1: Update PathItem

```python
from dataclasses import dataclass, field

@dataclass
class PathItem:
    path: Path
    file_type: FileType | None = None
    tags: set[str] = field(default_factory=set)
```

### Step 2: Update PathStep Base Class

```python
class PathStep(ABC):
    def __init__(self, name: str, input_tags: set[str] | None = None):
        self.name = name
        self.input_tags = input_tags or set()  # Empty set = process all items

    @abstractmethod
    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        pass
```

### Step 3: Update Pipeline

```python
class PathPipeline:
    def __init__(self, steps: list[PathStep]) -> None:
        self.steps = steps

    def run(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        active_items = items

        for step in self.steps:
            # Filter items if step has input_tags
            if step.input_tags:
                matching = {
                    k: v for k, v in active_items.items()
                    if step.input_tags & v.tags or not v.tags  # Also match untagged
                }
            else:
                matching = active_items

            if matching:
                print(f"▶ {step.name}...", end="", flush=True)
                new_items = step.process(matching)
                print(f" ({len(new_items)} items)")

                # Update active items with new/modified items
                active_items.update(new_items)

        return active_items
```

### Step 4: Example Step Implementation

```python
class ValidateFilesStep(PathStep):
    def __init__(self):
        super().__init__("validate_files", input_tags={"discovered"})

    def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
        result = {}

        for name, item in items.items():
            if self._is_valid(item):
                item.tags.add("valid")
                item.tags.discard("discovered")  # Optional: remove processed tag
            else:
                item.tags.add("invalid")
                item.tags.discard("discovered")

            result[name] = item

        return result

    def _is_valid(self, item: PathItem) -> bool:
        # Validation logic
        return item.path.exists() and item.path.stat().st_size > 0
```

### Step 5: Usage Example

```python
pipeline = PathPipeline([
    DiscoverFilesStep("discover"),  # Adds "discovered" tag
    ValidateFilesStep(),             # Processes "discovered", adds "valid"/"invalid"
    ProcessValidStep(),              # Processes "valid" only
    ErrorHandlerStep(),              # Processes "invalid" only
])

# Initial item needs no tags (discover step processes everything)
initial_items = {"data_dir": PathItem(Path("data/"))}
results = pipeline.run(initial_items)
```

---

## Open Questions

1. **Tag naming conventions**: Should there be a standard set of tags like "input", "valid", "invalid", "error"?
2. **Tag lifecycle**: Should tags accumulate or be replaced at each step?
3. **Backwards compatibility**: Should tag filtering be opt-in to maintain existing behavior?
4. **Multiple tag matches**: What if an item matches multiple steps' input tags?
5. **Logging/debugging**: How to track which items went through which steps?

---

## Next Steps

1. Prototype tag-based routing with a simple example
2. Run `make validate` to ensure type safety
3. Update tests to cover tag routing scenarios
4. Update documentation (README_pipe.md)
5. Consider adding visualization tools for tag flow
