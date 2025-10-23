# ==============================================================================
# Production RAG Framework - Makefile
# ==============================================================================
# Quick development commands for the project

.PHONY: help install install-dev test lint format check clean docker-up docker-down docker-logs pre-commit-install

# Default target
.DEFAULT_GOAL := help

# ==============================================================================
# Help
# ==============================================================================
help: ## Show this help message
	@echo "Production RAG Framework - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# Installation
# ==============================================================================
install: ## Install production dependencies
	uv pip install -r requirements.txt

install-dev: ## Install all dependencies including dev tools
	uv pip install -r requirements.txt -r requirements-dev.txt
	$(MAKE) pre-commit-install

install-editable: ## Install package in editable mode
	uv pip install -e ".[dev]"

sync: ## Sync dependencies using uv (recommended)
	uv sync

sync-dev: ## Sync all dependencies including dev tools
	uv sync --all-extras

# ==============================================================================
# Pre-commit Hooks
# ==============================================================================
pre-commit-install: ## Install pre-commit hooks
	pre-commit install
	pre-commit install --hook-type commit-msg

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks to latest versions
	pre-commit autoupdate

# ==============================================================================
# Code Quality
# ==============================================================================
format: ## Format code with black and isort
	black app tests
	isort app tests

lint: ## Run all linters (ruff, mypy, bandit)
	ruff check app tests
	mypy app
	bandit -c pyproject.toml -r app

lint-fix: ## Run linters with auto-fix
	ruff check --fix app tests
	black app tests
	isort app tests

check: ## Run all checks (format, lint, type check)
	$(MAKE) format
	$(MAKE) lint
	@echo "\n✅ All checks passed!"

# ==============================================================================
# Testing
# ==============================================================================
test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run only unit tests
	pytest tests/unit/ -v -m unit

test-integration: ## Run only integration tests
	pytest tests/integration/ -v -m integration

test-e2e: ## Run only end-to-end tests
	pytest tests/e2e/ -v -m e2e

test-cov: ## Run tests with coverage report
	pytest tests/ --cov=app --cov-report=html --cov-report=term --cov-report=xml

test-cov-unit: ## Run unit tests with coverage
	pytest tests/unit/ --cov=app --cov-report=html --cov-report=term -m unit

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -v

# ==============================================================================
# Docker
# ==============================================================================
docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start all services (Redis, Qdrant, API)
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-restart: ## Restart all services
	docker-compose restart

docker-logs: ## Show logs from all services
	docker-compose logs -f

docker-logs-api: ## Show API logs only
	docker-compose logs -f rag-api

docker-ps: ## Show running containers
	docker-compose ps

docker-clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all

# ==============================================================================
# Database
# ==============================================================================
db-up: ## Start only Redis and Qdrant
	docker-compose up -d redis qdrant

db-down: ## Stop database services
	docker-compose stop redis qdrant

db-reset: ## Reset all database data
	docker-compose down -v
	docker-compose up -d redis qdrant

# ==============================================================================
# Development
# ==============================================================================
run: ## Run the application locally
	python -m app.main

run-dev: ## Run with auto-reload
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run in production mode
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

shell: ## Start IPython shell with app context
	ipython -i -c "from app.core.config import get_settings; settings = get_settings()"

# ==============================================================================
# Cleanup
# ==============================================================================
clean: ## Remove all generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ dist/ build/ .coverage coverage.xml

clean-logs: ## Remove log files
	rm -rf logs/*.log

clean-all: clean clean-logs docker-clean ## Remove everything including Docker

# ==============================================================================
# Environment
# ==============================================================================
env-setup: ## Create .env from template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env from template. Please edit it with your API keys."; \
	else \
		echo "⚠️  .env already exists. Skipping."; \
	fi

env-validate: ## Validate environment configuration
	@python -c "from app.core.config import get_settings; settings = get_settings(); print('✅ Configuration valid')"

# ==============================================================================
# Documentation
# ==============================================================================
docs-serve: ## Serve API documentation locally
	@echo "Opening API documentation..."
	@echo "http://localhost:8000/docs"
	$(MAKE) run-dev

# ==============================================================================
# CI/CD
# ==============================================================================
ci: ## Run all CI checks
	$(MAKE) install-dev
	$(MAKE) lint
	$(MAKE) test-cov
	@echo "\n✅ All CI checks passed!"

ci-fast: ## Run quick CI checks (no coverage)
	$(MAKE) lint
	$(MAKE) test
	@echo "\n✅ Fast CI checks passed!"

# ==============================================================================
# Security
# ==============================================================================
security-scan: ## Run security scans
	bandit -c pyproject.toml -r app
	safety check --json || true

secrets-baseline: ## Create secrets baseline for detect-secrets
	detect-secrets scan > .secrets.baseline

# ==============================================================================
# Utilities
# ==============================================================================
outdated: ## Check for outdated dependencies
	uv pip list --outdated

upgrade-deps: ## Upgrade all dependencies (use with caution)
	uv pip install --upgrade -r requirements.txt -r requirements-dev.txt

tree: ## Show project structure
	@tree -I '__pycache__|*.pyc|.venv|venv|node_modules|.git|.pytest_cache|.mypy_cache|.ruff_cache|htmlcov|dist|build|*.egg-info' -L 3

check-ports: ## Check if required ports are available
	@echo "Checking ports..."
	@lsof -i:8000 && echo "⚠️  Port 8000 in use" || echo "✅ Port 8000 available"
	@lsof -i:6333 && echo "⚠️  Port 6333 in use" || echo "✅ Port 6333 available"
	@lsof -i:6379 && echo "⚠️  Port 6379 in use" || echo "✅ Port 6379 available"

# ==============================================================================
# Quick Start
# ==============================================================================
quick-start: ## Complete setup and run (first time setup)
	@echo "🚀 Starting quick setup..."
	$(MAKE) install-dev
	$(MAKE) env-setup
	$(MAKE) docker-up
	@echo "\n⏳ Waiting for services to be ready..."
	@sleep 5
	$(MAKE) run-dev

# ==============================================================================
# Aliases for Common Tasks
# ==============================================================================
up: docker-up ## Alias for docker-up
down: docker-down ## Alias for docker-down
logs: docker-logs ## Alias for docker-logs
restart: docker-restart ## Alias for docker-restart
