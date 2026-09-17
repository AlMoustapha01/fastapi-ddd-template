.DEFAULT_GOAL := help
UV := uv run

.PHONY: help install run up down migrate migration format lint test test.unit cov clean deps-graph

help: ## Show available commands
	@grep -E '^[a-zA-Z_.-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install dependencies and create .env from .env.example
	uv sync --group dev
	@test -f .env || cp .env.example .env

run: ## Run the API locally with auto-reload
	$(UV) uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000

up: ## Build and start PostgreSQL and the API with Docker Compose
	docker compose up -d --build

down: ## Stop the Docker Compose stack
	docker compose down

migrate: ## Apply database migrations
	$(UV) alembic upgrade head

migration: ## Generate a migration: make migration m="add something"
	@test -n "$(m)" || (echo 'Usage: make migration m="message"' && exit 1)
	$(UV) alembic revision --autogenerate -m "$(m)"

format: ## Format code and apply safe lint fixes
	$(UV) ruff format
	$(UV) ruff check --fix

lint: ## Run static checks
	$(UV) ruff format --check
	$(UV) ruff check
	$(UV) mypy
	$(UV) slotscheck src

test: ## Run all tests (integration tests need Docker)
	$(UV) pytest

test.unit: ## Run unit tests only
	$(UV) pytest -m "not integration"

cov: ## Run tests with a coverage report
	$(UV) coverage run -m pytest
	$(UV) coverage combine
	$(UV) coverage report

clean: ## Remove caches and build artifacts
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage .coverage.* htmlcov build dist

deps-graph: ## Print the Dishka dependency graph (d2 format)
	$(UV) python scripts/dishka/plot_dependencies_data.py
