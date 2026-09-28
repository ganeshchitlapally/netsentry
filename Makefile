# NetSentry task runner. Run from Linux, macOS or WSL2 (see README "Quickstart").
SHELL := /bin/bash
.DEFAULT_GOAL := help

UV ?= uv
RUN := $(UV) run

# Placeholder for targets whose phase has not landed yet: fail loudly, never fake success.
NOT_YET = @echo "make $@: not implemented yet (planned for $1)." >&2; exit 1

.PHONY: help setup data train eval serve bench agent-eval test lint format readme clean

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-11s\033[0m %s\n", $$1, $$2}'

setup: ## Create .venv from uv.lock (exact pins) and install pre-commit hooks
	$(UV) sync --locked
	@if [ -d .git ]; then $(RUN) pre-commit install; fi

data: ## Download UNSW-NB15 and verify checksums
	$(call NOT_YET,Phase 1)

train: ## Train baselines and anomaly detectors (logged to MLflow)
	$(call NOT_YET,Phase 2)

eval: ## Evaluate models on the test split and write results/
	$(call NOT_YET,Phase 2)

serve: ## Run the FastAPI scoring service
	$(call NOT_YET,Phase 3)

bench: ## Benchmark API latency/throughput into results/latency.json
	$(call NOT_YET,Phase 3)

agent-eval: ## Evaluate the LLM triage agent into results/agent_eval.json
	$(call NOT_YET,Phase 4)

readme: ## Regenerate README results tables from results/
	$(call NOT_YET,Phase 5)

test: ## Run tests (no dataset or API keys needed)
	$(RUN) pytest

lint: ## Ruff lint and format check
	$(RUN) ruff check .
	$(RUN) ruff format --check .

format: ## Auto-fix lint issues and format code
	$(RUN) ruff check --fix .
	$(RUN) ruff format .

clean: ## Remove caches (keeps data/, artifacts/, mlruns/)
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
