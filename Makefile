SHELL := /bin/sh

# Test selection
TEST_GROUP ?= unit
K8S_NAMESPACE ?= test

.DEFAULT_GOAL := help


# Helper
.PHONY: help

help:  ## Display this auto-generated help message
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


# Installation
.PHONY: update install

update:  ## Lock and install build dependencies
	poetry update

install:  ## Install build dependencies from lock file
	poetry install -E k8s -E api


# Development
.PHONY: clean format

clean:  ## Clean project from temp files / dirs
	find . -type d -name __pycache__ | xargs rm -rf

format:  ## Run pydocstyle docstring linter
	poetry run black .
	poetry run isort -rc .


# Testing
.PHONY: lint test

lint:  ## Run python linters
	poetry run black --check .
	poetry run isort --check-only -rc .
	poetry run pydocstyle .
	poetry run flake8 .
	poetry run mypy .

test:  ## Run pytest with grouped tests
	poetry run pytest tests/test_${TEST_GROUP}


# Deployment
.PHONY: k8s-apply

k8s-apply:  ## Update kubernetes resources
	kubectl -n ${K8S_NAMESPACE} apply -f kubernetes/
