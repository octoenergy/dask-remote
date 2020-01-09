K8S_NAMESPACE=test

install:
	poetry install

black:
	poetry run isort -rc -y .
	poetry run black .

lint:
	poetry run flake8 .
	poetry run pydocstyle .
	poetry run mypy .

test:
	poetry run pytest tests --host=$(shell minikube ip)

k8s-apply:
	kubectl -n ${K8S_NAMESPACE} apply -f kubernetes/

setup-py:  # create a setup.py for editable installs
	dephell deps convert
