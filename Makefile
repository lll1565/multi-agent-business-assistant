.PHONY: install install-dev backend backend-prod frontend dev test lint format typecheck arch-test frontend-test frontend-lint frontend-typecheck pre-commit-install ci

PYTHON ?= python
NPM ?= npm

MYPY_STONE_CORE = src/subagent/stone/routing/registry.py src/subagent/stone/routing/classifier.py \
	src/subagent/stone/routing/routing_intents.py src/subagent/stone/routing/routing_types.py \
	src/subagent/stone/routing/api_fastpath.py src/subagent/stone/persistence/checkpointer.py \
	src/subagent/stone/routing/hard_route.py src/subagent/stone/routing/resolve_route.py \
	src/subagent/stone/runtime/core.py src/subagent/stone/runtime/turn_runner.py

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

backend:
	$(PYTHON) -m uvicorn backend.main:app --host 127.0.0.1 --port 8010 --reload --reload-dir src/backend

backend-prod:
	$(PYTHON) -m backend.cli

frontend:
	cd frontend && $(NPM) run dev

dev:
	@echo "Use scripts/run_all.ps1 on Windows, or run 'make backend' and 'make frontend' in two terminals."

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src/backend src/subagent tests

format:
	$(PYTHON) -m ruff format src/backend src/subagent tests

format-check:
	$(PYTHON) -m ruff format --check src/backend src/subagent tests

typecheck:
	$(PYTHON) -m mypy backend
	$(PYTHON) -m mypy $(MYPY_STONE_CORE)

arch-test:
	$(PYTHON) -m pytest -q tests/backend/test_architecture.py

frontend-test:
	cd frontend && $(NPM) run test

frontend-lint:
	cd frontend && $(NPM) run lint

frontend-typecheck:
	cd frontend && $(NPM) run typecheck

pre-commit-install:
	$(PYTHON) -m pre_commit install

ci: lint format-check typecheck test arch-test frontend-lint frontend-typecheck frontend-test
