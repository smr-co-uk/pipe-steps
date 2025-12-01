# Project Setup Guide

This document provides instructions for setting up the pipe-steps development environment and configuring git hooks.

## Installation

### Prerequisites

- Python 3.12 or later
- Git

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/pipe-steps.git
cd pipe-steps

# Install dependencies using uv
uv sync

# Install git hooks (see below)
git config core.hooksPath .githooks
```

### Using Different Installation Methods

#### Option 1: Direct pip from GitHub (recommended for users)
```bash
pip install git+https://github.com/yourusername/pipe-steps.git
```

#### Option 2: Clone and use uv (recommended for development)
```bash
git clone https://github.com/yourusername/pipe-steps.git
cd pipe-steps
uv sync
```

#### Option 3: Editable install with uv
```bash
git clone https://github.com/yourusername/pipe-steps.git
cd pipe-steps
uv pip install -e .
```

---

## Git Hooks Setup

### What are Git Hooks?

Git hooks are scripts that run automatically at certain points in the git workflow. This project includes a pre-commit hook that ensures code quality before commits.

### Installing Git Hooks

The project includes a pre-commit hook in the `.githooks/` directory. To enable it:

```bash
git config core.hooksPath .githooks
```

This tells git to look for hooks in the `.githooks/` directory instead of the default `.git/hooks/`.

### Pre-Commit Hook

**File:** `.githooks/pre-commit`

**What it does:**
- Runs `make validate` before each commit
- Performs type checking, format checking, tests, and coverage analysis
- Prevents commits if any check fails

**When it runs:**
- Automatically when you run `git commit`
- Runs on all staged changes

### Using the Pre-Commit Hook

#### Normal commit flow (with validation):
```bash
git add .
git commit -m "Your commit message"
# If validation passes, commit is created
# If validation fails, commit is rejected with error details
```

#### Bypassing the hook (not recommended):
```bash
git commit --no-verify -m "Your commit message"
```

### Hook Output Example

**Successful commit:**
```
🔍 Running pre-commit validation...

uv run mypy src/pipe_steps
Success: no issues found in 24 source files
uv run pyright
0 errors, 0 warnings, 0 informations
✓ All type checkers passed!
...
============================== 39 passed in 0.36s ==============================
✓ Coverage report: htmlcov/index.html
✓ Full validation complete!

Summary:
  ✓ Type checking passed (mypy + pyright)
  ✓ Format checking passed (isort + black)
  ✓ Tests passed with coverage report

Coverage report: htmlcov/index.html

✅ Pre-commit validation passed!
```

**Failed commit:**
```
🔍 Running pre-commit validation...

... (validation output)

❌ Pre-commit validation failed!

Please fix the issues above and try again.
To bypass this check (not recommended), use: git commit --no-verify
```

---

## Development Workflow

### Running Quality Checks Manually

```bash
# Type checking
make typecheck

# Format checking
make format-check

# Format code
make format

# Run tests
make test

# Generate coverage report
make coverage

# Run all checks (type, format, test, coverage)
make validate

# Quick test + lint
make check
```

### Before Committing

Make sure your changes pass validation:

```bash
# Run all quality checks
make validate

# Fix any formatting issues
make format

# Then commit (pre-commit hook will validate again)
git add .
git commit -m "Your commit message"
```

### Creating a New Feature

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature

# 2. Make your changes
# ... edit files ...

# 3. Run validation
make validate

# 4. If validation fails:
make format        # Fix formatting
# ... fix any type errors or test failures ...
make validate      # Check again

# 5. Commit changes (pre-commit hook runs make validate)
git add .
git commit -m "Add your feature"

# 6. Push to remote
git push origin feature/your-feature

# 7. Create pull request on GitHub
```

---

## Makefile Targets Reference

### Quality Assurance

| Target | Purpose |
|--------|---------|
| `make typecheck` | Run mypy and pyright type checkers |
| `make format-check` | Check code formatting without modifying |
| `make format` | Format code with isort and black |
| `make lint` | Run typecheck + format-check |
| `make test` | Run test suite |
| `make coverage` | Run tests with coverage report (HTML) |
| `make check` | Run tests and linting |
| `make validate` | Full QA: typecheck, lint, test, coverage |

### Other Targets

| Target | Purpose |
|--------|---------|
| `make clean` | Remove build artifacts and cache |
| `make build` | Build distributable package |
| `make install` | Install in editable mode |
| `make all` | Clean, check, and build |
| `make help` | Show all available targets |

---

## Running Examples

Each pipeline has a demonstration script:

```bash
# Checkpoint Pipeline demo
python -m pipe_steps.checkpoint.main_checkpoint

# Batch Pipeline demo
python -m pipe_steps.batch.main_batch

# Path Pipeline demo
python -m pipe_steps.path.main_pipe
```

Or use the installed CLI scripts:

```bash
checkpoint-pipeline
batch-pipeline
path-pipeline
```

---

## Testing

### Run All Tests
```bash
make test
```

### Run Specific Test File
```bash
pytest tests/unit/checkpoint/test_checkpoint_pipeline.py -v
```

### Run Specific Test Class
```bash
pytest tests/unit/checkpoint/test_checkpoint_pipeline.py::TestCheckpointPipeline -v
```

### Run Specific Test Method
```bash
pytest tests/unit/checkpoint/test_checkpoint_pipeline.py::TestCheckpointPipeline::test_simple_execution -v
```

### Generate Coverage Report
```bash
make coverage
# Open htmlcov/index.html in browser
```

---

## Troubleshooting

### Pre-commit hook won't run

**Solution 1:** Make sure you've configured git to use the custom hooks path:
```bash
git config core.hooksPath .githooks
```

**Solution 2:** Check that the hook file is executable:
```bash
ls -la .githooks/pre-commit
# Should show -rwx------
```

### Make validate takes too long

This is normal! The validate target runs:
- Type checking (mypy + pyright)
- Format checking
- All tests (39 tests)
- Coverage analysis

You can run individual checks while developing:
```bash
make test          # Just tests (faster)
make typecheck     # Just type checking
```

### Tests are failing locally but passing in CI

Possible causes:
- Different Python version (CI uses 3.11 and 3.12)
- Different dependency versions
- Platform-specific issues

Solution:
```bash
# Check Python version
python --version

# Ensure dependencies are up to date
uv sync

# Run full validation
make validate
```

### Type errors even after formatting

Some type errors require code changes, not just formatting:
```bash
make typecheck     # See detailed error messages
# Fix the code issues
make validate      # Verify it's fixed
```

---

## Best Practices

1. **Always run `make validate` before committing**
   - Prevents unfinished work from being committed
   - Catches issues early

2. **Use `make format` to auto-fix formatting issues**
   - Saves time on style corrections
   - Ensures consistent code style

3. **Review test failures carefully**
   - Read the full error message
   - Check if it's a real issue or a test setup problem

4. **Keep dependencies updated**
   - Run `uv sync` after pulling changes
   - Check for new type checking issues

5. **Write tests for new features**
   - Maintain test coverage above 60%
   - Test both happy path and edge cases

---

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **test.yml**: Runs on all branches except main
  - Tests on Python 3.11 and 3.12
  - Uploads coverage to Codecov

- **main.yml**: Runs on main branch only
  - Tests then builds distribution package
  - Uploads artifacts

- **tag-release.yml**: Manual trigger
  - Creates semantic version tags
  - Creates GitHub releases

See `.github/workflows/` for detailed configurations.

---

## Project Documentation

- **README.md** - Main project overview
- **README_checkpoint.md** - Checkpoint Pipeline documentation
- **README_batch.md** - Batch Pipeline documentation
- **README_pipe.md** - Path Pipeline documentation
- **PROMPTS.md** - Record of this session's prompts
- **PRIOR_SESSION_SUMMARY.md** - Summary of previous session
- **SETUP.md** - This file

---

## Questions or Issues?

If you encounter any issues:

1. Check this SETUP.md guide
2. Review the relevant README for your pipeline type
3. Check the Makefile help: `make help`
4. Review GitHub Issues (if applicable)

Happy coding! 🚀
