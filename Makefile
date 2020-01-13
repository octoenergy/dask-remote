K8S_NAMESPACE=test

# Test selectopm
TEST_GROUP ?= unit

.PHONY: clean setup-py install format lint test

clean:
	find . | grep -E '(__pycache__|\.pyc|\.pyo$$)' | xargs rm -rf

setup-py:  # create a setup.py for editable installs
	dephell deps convert

install:
	poetry install

format:
	poetry run isort -rc -y .
	poetry run black .

lint:
	poetry run flake8 .
	poetry run pydocstyle .
	poetry run mypy .

test:
	poetry run pytest tests/test_${TEST_GROUP} --host=$(shell minikube ip)

.PHONY: k8s-apply

k8s-apply:
	kubectl -n ${K8S_NAMESPACE} apply -f kubernetes/
