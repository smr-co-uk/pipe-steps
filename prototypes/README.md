# DAG Routing Prototypes

This directory contains working prototypes for two different approaches to adding DAG-based routing to the PathPipeline.

## Overview

Both solutions address the requirement from `DAG.md` to enable branching and routing of PathItems through different processing steps, particularly for success/failure handling.

## Solutions

### [Solution 2: Tag-Based Routing](solution2_tags/)

**Items carry tags, steps subscribe to tags, automatic routing.**

```python
# Add tags to items
item.tags.add("valid")
item.tags.add("large_file")

# Steps filter by tags
class ProcessStep(PathStep):
    def __init__(self):
        super().__init__("process", input_tags={"valid"})
```

**Best for:**
- Simple success/failure routing
- Dynamic, data-driven routing
- Quick prototyping
- Teams new to pipeline concepts

[📖 Full Documentation](solution2_tags/README.md)

---

### [Solution 4: Graph-Based DAG](solution4_graph/)

**Explicit DAG with nodes, edges, and topological execution.**

```python
# Explicit connections
pipeline.add_step("validate", ValidateStep())
pipeline.add_step("process", ProcessStep())
pipeline.connect("validate", "process", "valid", "input")
```

**Best for:**
- Parallel execution needs
- Complex dependency chains
- Production data platforms
- Teams familiar with Airflow/Luigi

[📖 Full Documentation](solution4_graph/README.md)

---

## Quick Comparison

| Feature | Solution 2 (Tags) | Solution 4 (Graph) |
|---------|-------------------|-------------------|
| **Complexity** | 🟢 Low | 🔴 High |
| **Learning Curve** | 🟢 5-10 min | 🟡 30-60 min |
| **Code to Write** | 🟢 50-100 lines | 🔴 200-300 lines |
| **Type Safety** | 🟡 Runtime | 🟢 Compile-time |
| **Flexibility** | 🟢 High | 🟡 Medium |
| **Dynamic Routing** | 🟢 Excellent | 🔴 Limited |
| **Parallel Execution** | 🔴 No | 🟢 Yes |
| **Cycle Detection** | 🔴 No | 🟢 Yes |
| **Visualization** | 🟡 Implicit | 🟢 Explicit |
| **Best for Production** | 🟡 Small/Medium | 🟢 Large Scale |

## Running the Prototypes

### Solution 2 (Tag-Based)

```bash
cd solution2_tags
python demo.py
```

Demonstrates:
- Basic success/failure routing
- Parallel branches (file types)
- Dynamic routing (size-based)

### Solution 4 (Graph-Based)

```bash
cd solution4_graph
python demo.py
```

Demonstrates:
- Basic DAG with success/failure branches
- Parallel branches with merge
- Complex multi-split DAG
- Cycle detection

## Detailed Analysis

See these documents for comprehensive analysis:

- [`DAG_analysis_01.md`](../DAG_analysis_01.md) - Initial analysis of all 4 solutions
- [`DAG_tradeoffs_2_vs_4.md`](../DAG_tradeoffs_2_vs_4.md) - Deep dive comparing Solutions 2 and 4

## Code Examples

### Solution 2: Simple Success/Failure

```python
pipeline = PathPipeline([
    DiscoverFilesStep(),        # Adds "discovered" tag
    ValidateFilesStep(),        # Adds "valid" or "invalid" tag
    ProcessValidFilesStep(),    # Processes items with "valid" tag
    ErrorHandlerStep(),         # Processes items with "invalid" tag
])
```

### Solution 4: DAG with Parallel Branches

```python
pipeline = PathPipeline()

# Add steps
pipeline.add_step("discover", DiscoverFilesStep())
pipeline.add_step("filter", FilterByTypeStep())
pipeline.add_step("csv", ProcessCSVStep())
pipeline.add_step("parquet", ProcessParquetStep())
pipeline.add_step("merge", MergeStep(["csv", "parquet"]))

# Connect (creates parallel branches)
pipeline.connect("discover", "filter", "output", "input")
pipeline.connect("filter", "csv", "csv", "input")
pipeline.connect("filter", "parquet", "parquet", "input")
pipeline.connect("csv", "merge", "output", "csv")
pipeline.connect("parquet", "merge", "output", "parquet")
```

## Recommendation

**Start with Solution 2 (Tag-Based)** unless you:
- Need parallel execution for performance
- Have complex dependency chains
- Require compile-time validation
- Are building a large-scale production system

Solution 2 is simpler, more flexible, and easier to maintain for most use cases. You can always migrate to Solution 4 later if you hit performance bottlenecks or need the additional structure.

## Migration Path

1. **Phase 1**: Implement Solution 2 (tag-based)
   - Get basic routing working
   - Validate the approach with real use cases

2. **Phase 2**: Optimize hot paths
   - Profile to find bottlenecks
   - Identify independent branches that could benefit from parallelism

3. **Phase 3**: Hybrid or migrate to Solution 4 if needed
   - Keep simple paths using tags
   - Use graph-based DAG for complex/parallel sections
   - Or fully migrate if parallel execution is critical

## Implementation Notes

### Type Safety

Both prototypes use full type hints and can be validated with mypy/pyright:

```bash
mypy solution2_tags/*.py
mypy solution4_graph/*.py
```

### Testing

Both approaches are highly testable:

**Solution 2:**
```python
def test_routing():
    step = ValidateStep()
    items = {"f1": PathItem(path=Path("test.csv"), tags={"discovered"})}
    result = step.process(items)
    assert "valid" in result["f1"].tags
```

**Solution 4:**
```python
def test_connections():
    pipeline = PathPipeline()
    pipeline.add_step("s1", Step1())
    pipeline.add_step("s2", Step2())
    pipeline.connect("s1", "s2", "output", "input")
    assert len(pipeline.connections) == 1
```

## Architecture Integration

Both solutions fit within the existing `pipe-steps` architecture:

```
src/pipe_steps/
├── checkpoint/     # Existing: In-memory with checkpointing
├── batch/          # Existing: Streaming with frontier
└── path/           # TO BE UPDATED with chosen solution
    ├── path_item.py              # Add tags (Solution 2) or keep as-is (Solution 4)
    ├── path_step.py              # Update base class
    ├── path_pipeline.py          # Update pipeline logic
    └── ...
```

## Next Steps

1. **Review both prototypes** - Run the demos, read the code
2. **Consider your use case** - Do you need parallelism? Complex routing?
3. **Choose a solution** - Based on your requirements
4. **Integrate into main codebase** - Update the `path` package
5. **Write tests** - Ensure routing works as expected
6. **Update documentation** - Update README_pipe.md

## Questions?

See the detailed analysis documents or examine the prototype code directly. Both prototypes are fully functional and demonstrate the key concepts.
