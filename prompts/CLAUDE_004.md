# CLAUDE_004 - Path Pipeline Dictionary Interface Refactor

## Description

Refactored the path pipeline to use a dictionary-based interface where each PathItem is mapped to a unique string key, replacing the previous list-based approach. This change provides better organization and flexibility, allowing steps to add, remove, or rename PathItems through dictionary operations.

## What Changed

- **Interface**: Changed from `list[PathItem]` to `dict[str, PathItem]`
- **Rationale**: Since PathItem can represent either a file or directory, using a dictionary eliminates the need for lists while providing named access to each item
- **Step Behavior**:
  - `DiscoverFilesStep`: Adds new entries for discovered files using file path strings as keys
  - `FilterByTypeStep`: Removes non-matching entries from the dictionary
- **All components updated**: Base classes, concrete steps, pipeline, tests, and demo script

## User Prompts

### Prompt 1
```
can you modifiy the path pipeline so that instead of an input list of PathItem and an
output list of PathItem we have a dictionary of named PathItems for both input and
output it will be responsibility of each PathStep to use the dictionary of paths as
it requires
```

### Prompt 2
```
not quite right: the interface should be 'def process(self, items: dict[str, PathItem])
-> dict[str, PathItem]:' as PathItem can refer to a file or a directory so having a
list is unnecessary
```

### Prompt 3
```
can save my prompts to prompts/CLAUDE_004.md with a brief description of what it did
```

## Files Modified

1. `src/pipe_steps/path/path_step.py` - Updated abstract base class signature
2. `src/pipe_steps/path/path_pipeline.py` - Updated pipeline run() method
3. `src/pipe_steps/path/discover_files_step.py` - Refactored to work with dictionary
4. `src/pipe_steps/path/filter_by_type_step.py` - Refactored to filter dictionary entries
5. `src/pipe_steps/path/main_pipe.py` - Updated all demo scenarios
6. `tests/unit/path/test_path_pipeline.py` - Updated all 11 test cases

## Validation

All checks passed:
- Type checking (mypy + pyright): ✓
- Formatting (isort + black): ✓
- Tests (38 total, all passing): ✓
