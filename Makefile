.PHONY: help install dev test lint format type-check security complexity fuzz pip-compile clean examples demo check

PYTHON ?= python3
POETRY ?= poetry
VHS ?= vhs

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(POETRY) install --only main

dev: ## Install all dependencies (including dev)
	$(POETRY) install

test: ## Run tests
	$(POETRY) run pytest tests/ -v

lint: ## Run linters (ruff + black check)
	$(POETRY) run ruff check camt053_lsp/ tests/ benches/ scripts/ fuzz/ examples/
	$(POETRY) run black --check camt053_lsp/ tests/ benches/ scripts/ fuzz/ examples/

format: ## Auto-format code (ruff fix + black)
	$(POETRY) run ruff check --fix camt053_lsp/ tests/ benches/ scripts/ fuzz/ examples/
	$(POETRY) run black camt053_lsp/ tests/ benches/ scripts/ fuzz/ examples/

type-check: ## Run mypy type checking
	$(POETRY) run mypy camt053_lsp/

security: ## Run security scan (bandit)
	$(POETRY) run bandit -r camt053_lsp/ -ll

complexity: ## Check per-function complexity against complexity-baseline.json
	$(POETRY) run python scripts/check_complexity.py

fuzz: ## Run the Atheris fuzz harness locally (set RUNS to override)
	$(PYTHON) -m pip install atheris
	$(PYTHON) fuzz/fuzz_parser.py -atheris_runs=$(or $(RUNS),100000)

pip-compile: ## Regenerate hash-pinned requirements/*.txt from requirements/*.in
	@command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
	@for f in requirements/*.in; do \
		case "$$f" in requirements/build.in|requirements/audit.in) continue ;; esac; \
		echo "compiling $$f"; \
		uv pip compile --quiet --generate-hashes --universal \
			--python-version 3.10 "$$f" -o "$${f%.in}.txt"; \
	done
	@# build.in and audit.in are installed only on Python 3.12 (filelock 4.2.1 needs 3.11).
	@for f in requirements/build.in requirements/audit.in; do \
		echo "compiling $$f (3.12)"; \
		uv pip compile --quiet --generate-hashes --universal \
			--python-version 3.12 "$$f" -o "$${f%.in}.txt"; \
	done

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .eggs/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/
	rm -rf coverage.xml .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

demo: ## Render .github/demo.gif from .github/demo.tape with VHS
	$(POETRY) run $(VHS) .github/demo.tape

examples: ## Verify example scripts run
	$(POETRY) run python examples/lsp_helpers.py

check: lint type-check security complexity test examples ## Run all checks
