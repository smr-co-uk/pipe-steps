.PHONY: help clean test build install lint format check typecheck mypy pyright coverage format-check validate all

help:
	@echo "Available targets:"
	@echo "  make clean        - Remove build artifacts and cache"
	@echo "  make test         - Run the test suite"
	@echo "  make coverage     - Run tests and generate coverage report"
	@echo "  make typecheck    - Run all type checkers (mypy + pyright)"
	@echo "  make mypy         - Run mypy type checker"
	@echo "  make pyright      - Run pyright type checker"
	@echo "  make format       - Format code with isort and black"
	@echo "  make format-check - Check formatting without modifying"
	@echo "  make lint         - Run linting (typecheck + format check)"
	@echo "  make check        - Run tests and linting"
	@echo "  make validate     - Full QA: typecheck, lint, test, and coverage"
	@echo "  make build        - Build distributable package"
	@echo "  make install      - Install package in editable mode"
	@echo "  make all          - Clean, check, and build"

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

test:
	uv run pytest -v --cov=pipe_steps

coverage:
	uv run pytest --cov=pipe_steps --cov-report=html
	@echo "✓ Coverage report: htmlcov/index.html"

mypy:
	uv run mypy src/pipe_steps

pyright:
	uv run pyright

typecheck: mypy pyright
	@echo "✓ All type checkers passed!"

format:
	uv run isort src/ tests/
	uv run black src/ tests/

format-check:
	uv run isort --check-only src/ tests/
	uv run black --check src/ tests/

lint: typecheck format-check
	@echo "✓ Linting complete!"

check: test lint

validate: typecheck format-check coverage
	@echo "✓ Full validation complete!"
	@echo ""
	@echo "Summary:"
	@echo "  ✓ Type checking passed (mypy + pyright)"
	@echo "  ✓ Format checking passed (isort + black)"
	@echo "  ✓ Tests passed with coverage report"
	@echo ""
	@echo "Coverage report: htmlcov/index.html"

build: clean
	uv build

install:
	uv pip install -e .

all: clean check build
	@echo "✓ Clean, test, lint, and build complete!"
