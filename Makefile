SHELL := /bin/sh -e

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
.PHONY: clean format setup-py

clean:  ## Clean project from temp files / dirs
	find src -type d -name __pycache__ | xargs rm -rf

format:  ## Run pydocstyle docstring linter
	poetry run black src
	poetry run isort -rc src

setup-py:  ## Create project `setup.py` for editable installs
	poetry run dephell deps convert


# Testing
.PHONY: lint test

lint:  ## Run python linters
	poetry run black --check src
	poetry run isort --check-only -rc src
	poetry run pydocstyle src
	poetry run flake8 src
	poetry run mypy src

test:  ## Run pytest with grouped tests
	poetry run pytest src/tests/test_${TEST_GROUP}


# Deployment
.PHONY: k8s-apply

k8s-apply:  ## Update kubernetes resources
	kubectl -n ${K8S_NAMESPACE} apply -f kubernetes/
