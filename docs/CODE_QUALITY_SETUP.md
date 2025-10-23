# Code Quality & Pre-commit Setup

## Overview

The project now includes comprehensive code quality tools with pre-commit hooks to enforce standards before every commit.

## What Was Implemented

### 1. Pre-commit Hooks (`.pre-commit-config.yaml`)

Automatic checks that run before every commit:

#### Code Formatting
- **Black** - Python code formatter (line-length: 100)
- **isort** - Import sorting

#### Linting
- **Ruff** - Fast Python linter (replaces flake8, pylint, etc.)
- **mypy** - Static type checking

#### Security
- **Bandit** - Security vulnerability scanner
- **detect-secrets** - Prevents committing secrets

#### General Checks
- Check for large files (>500KB)
- Check YAML/JSON/TOML syntax
- Fix end-of-file issues
- Trim trailing whitespace
- Prevent commits to main/master
- Check for debug statements
- Markdown linting

### 2. Tool Configurations (`pyproject.toml`)

Centralized configuration for all tools:

#### Black
```toml
line-length = 100
target-version = ['py311']
```

#### Ruff
- 20+ rule sets enabled
- Fast linting for Python code
- Auto-fix capabilities
- Import sorting

#### mypy
- Type checking enabled
- Strict optional checking
- Warn on unused code

#### pytest
- Test discovery configuration
- Markers for test types (unit, integration, e2e)
- Coverage settings (70% minimum)

### 3. Makefile Commands

Quick commands for development:

```bash
# Installation
make install          # Install production deps
make install-dev      # Install dev deps + pre-commit hooks
make install-editable # Install in editable mode

# Code Quality
make format           # Format code (black + isort)
make lint             # Run all linters
make lint-fix         # Run linters with auto-fix
make check            # Run all checks

# Testing
make test             # Run all tests
make test-unit        # Run unit tests only
make test-integration # Run integration tests only
make test-cov         # Run tests with coverage
make test-watch       # Run tests in watch mode

# Docker
make docker-up        # Start all services
make docker-down      # Stop all services
make docker-logs      # View logs
make db-up            # Start only Redis & Qdrant

# Development
make run              # Run application
make run-dev          # Run with auto-reload
make run-prod         # Run production mode
make shell            # Start IPython shell

# Cleanup
make clean            # Remove generated files
make clean-all        # Remove everything including Docker

# Pre-commit
make pre-commit-install  # Install hooks
make pre-commit-run      # Run on all files
make pre-commit-update   # Update hooks

# CI/CD
make ci               # Run all CI checks
make ci-fast          # Quick CI checks

# Security
make security-scan    # Run security scans
make secrets-baseline # Create secrets baseline

# Quick Start
make quick-start      # Complete setup and run
```

## Getting Started

### 1. Install Pre-commit Hooks

```bash
# Install development dependencies
make install-dev

# Or manually
pip install -r requirements-dev.txt
pre-commit install
```

### 2. Run Pre-commit Manually

```bash
# Run on all files
make pre-commit-run

# Or run specific hook
pre-commit run black --all-files
pre-commit run ruff --all-files
```

### 3. Format Code

```bash
# Auto-format all code
make format

# Or run tools individually
black app tests
isort app tests
```

### 4. Run Linters

```bash
# Run all linters
make lint

# Or with auto-fix
make lint-fix
```

### 5. Run Type Checker

```bash
# Type check with mypy
mypy app

# Or use Makefile
make lint
```

## Pre-commit Workflow

### What Happens on Commit

When you run `git commit`, pre-commit automatically:

1. **Formats your code** (Black + isort)
2. **Lints your code** (Ruff)
3. **Type checks** (mypy)
4. **Scans for security issues** (Bandit)
5. **Checks for secrets** (detect-secrets)
6. **Validates file syntax** (YAML, JSON, TOML)
7. **Fixes common issues** (trailing whitespace, EOF)

### If Checks Fail

```bash
# Pre-commit will show errors
# Fix them and try committing again

# To bypass (NOT RECOMMENDED)
git commit --no-verify -m "message"

# Better: Fix issues
make format
make lint-fix
git add .
git commit -m "message"
```

## Tool Details

### Black (Code Formatter)

Opinionated code formatter:
- Line length: 100 characters
- Automatic formatting
- No configuration needed

```bash
# Format all code
black app tests

# Check without changing
black --check app tests
```

### Ruff (Linter)

Super fast Python linter:
- Replaces: flake8, pylint, isort, pyupgrade, and more
- 20+ rule sets enabled
- Auto-fix capabilities

```bash
# Lint with auto-fix
ruff check --fix app tests

# Just check
ruff check app tests
```

### mypy (Type Checker)

Static type checking:
- Catches type errors
- Improves code quality
- Optional but recommended

```bash
# Type check
mypy app

# Ignore missing imports
mypy --ignore-missing-imports app
```

### Bandit (Security Scanner)

Security vulnerability scanner:
- Detects common security issues
- SQL injection risks
- Hardcoded passwords
- etc.

```bash
# Scan for security issues
bandit -c pyproject.toml -r app
```

### detect-secrets

Prevents committing secrets:
- API keys
- Passwords
- Tokens
- etc.

```bash
# Create baseline
make secrets-baseline

# Scan for secrets
detect-secrets scan
```

## Configuration Files

### `.pre-commit-config.yaml`
Pre-commit hook configuration

### `pyproject.toml`
All tool configurations in one file:
- Black settings
- Ruff rules
- mypy options
- pytest configuration
- Coverage settings
- Bandit security rules
- isort settings

### `.secrets.baseline`
Baseline for detect-secrets (committed)

### `Makefile`
Development commands

## CI/CD Integration

### GitHub Actions Example

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: make install-dev

      - name: Run CI checks
        run: make ci
```

### Pre-commit CI

```yaml
# .pre-commit-ci.yaml
repos:
  - repo: meta
    hooks:
      - id: check-hooks-apply
      - id: check-useless-excludes
```

## Best Practices

### 1. Run Checks Before Pushing

```bash
# Quick check
make check

# Or full CI
make ci
```

### 2. Keep Hooks Updated

```bash
# Update to latest versions
make pre-commit-update

# Or manually
pre-commit autoupdate
```

### 3. Format Code Regularly

```bash
# Format before committing
make format
```

### 4. Fix Issues, Don't Skip

```bash
# ❌ Bad: Skip checks
git commit --no-verify

# ✅ Good: Fix issues
make lint-fix
git add .
git commit
```

### 5. Use Markers in Tests

```python
import pytest

@pytest.mark.unit
def test_something():
    assert True

@pytest.mark.integration
def test_integration():
    assert True

@pytest.mark.slow
def test_slow_operation():
    assert True
```

Then run specific tests:
```bash
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m "not slow"    # Skip slow tests
```

## Troubleshooting

### Pre-commit Hooks Not Running

```bash
# Reinstall hooks
pre-commit install

# Check installation
pre-commit --version
```

### Hook Fails on Commit

```bash
# Run manually to see details
pre-commit run --all-files

# Fix specific hook
pre-commit run black --all-files
```

### Update Hooks

```bash
# Update to latest versions
pre-commit autoupdate

# Clean cache
pre-commit clean
```

### Skip Specific Hook

```bash
# Skip specific hook (temporary)
SKIP=mypy git commit -m "message"

# Skip all hooks (NOT RECOMMENDED)
git commit --no-verify -m "message"
```

## Summary

✅ **Implemented:**
- Pre-commit hooks for automated checks
- Code formatting (Black + isort)
- Linting (Ruff)
- Type checking (mypy)
- Security scanning (Bandit + detect-secrets)
- Comprehensive Makefile
- Centralized configuration (pyproject.toml)

✅ **Benefits:**
- Consistent code quality
- Catch errors before commit
- Automated formatting
- Security vulnerability detection
- Easy development workflow

✅ **Quick Start:**
```bash
make install-dev      # Install everything
make check            # Run all checks
make test-cov         # Run tests with coverage
make quick-start      # Complete setup
```

The code quality infrastructure is now production-ready! 🎉
