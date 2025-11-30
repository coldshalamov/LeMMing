.PHONY: help install test lint format typecheck clean run bootstrap

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install package and dependencies
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev,api,llm]"

test:  ## Run tests with coverage
	pytest

test-v:  ## Run tests with verbose output
	pytest -v

test-vv:  ## Run tests with very verbose output
	pytest -vv

coverage:  ## Generate HTML coverage report
	pytest --cov=lemming --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:  ## Run ruff linter
	ruff check lemming tests

lint-fix:  ## Run ruff linter and fix issues
	ruff check --fix lemming tests

format:  ## Format code with black
	black lemming tests

format-check:  ## Check code formatting
	black --check lemming tests

typecheck:  ## Run type checking with mypy
	mypy lemming

check-all: lint typecheck test  ## Run all checks (lint, typecheck, test)

clean:  ## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

bootstrap:  ## Bootstrap LeMMing configuration
	python -m lemming.cli bootstrap

run:  ## Run LeMMing engine
	python -m lemming.cli run

run-once:  ## Run a single turn
	python -m lemming.cli run-once

build:  ## Build distribution packages
	python -m build

.DEFAULT_GOAL := help
