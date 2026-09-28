VENV := .venv
PY := $(VENV)/bin/python

.DEFAULT_GOAL := help

.PHONY: help setup hooks env check test lint djlint audit

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: env ## Create .venv, install dev+test deps, and activate the git hooks
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements/dev.txt
	$(PY) -m pip install -r requirements/test.txt
	$(PY) -m pre-commit install --install-hooks
	# core.hooksPath is set below, so `pre-commit install` above only
	# populates the hook environments; it does not wire a second hook.
	git config core.hooksPath .githooks

env: ## Generate the .env if it is missing (never overwrites an existing one)
	@if [ -f .env ]; then \
		echo ".env ya existe: no se toca (para regenerar: make env-force)"; \
	else \
		$(PY) scripts/generate_env.py --development; \
	fi

env-force: ## Regenerate the .env, keeping the current key pair
	$(PY) scripts/generate_env.py --development --force

hooks: ## Point git at the versioned hooks in .githooks/
	git config core.hooksPath .githooks

check: ## Run the Django system check
	$(PY) manage.py check

test: ## Run the full Django test suite
	$(PY) manage.py test

lint: ## Run ruff check and ruff format --check
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

djlint: ## Lint Django templates
	$(VENV)/bin/djlint . --lint

audit: ## Audit the runtime dependencies for known CVEs
	$(VENV)/bin/pip-audit -r requirements/base.txt
