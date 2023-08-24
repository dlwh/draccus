.PHONY: help check autoformat test
.DEFAULT: help

# Generates a useful overview/help message for various make features - add to this as necessary!
help:
	@echo "make check"
	@echo "    Run code style and linting (black, ruff) *without* changing files!"
	@echo "make autoformat"
	@echo "    Run code styling (black, ruff) and update in place - committing with pre-commit also does this."
	@echo "make test"
	@echo "    Run tests via pytest (requires installing dev dependencies)."

check:
	black --check .
	ruff check --show-source .

autoformat:
	black .
	ruff check --fix --show-fixes .

test:
	pytest tests
