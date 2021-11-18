SHELL := /bin/bash
MAX_LINE_LENGTH := 119
POETRY_VERSION := $(shell poetry --version 2>/dev/null)

help: ## List all commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9 -]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check-poetry:
	@if [[ "${POETRY_VERSION}" == *"Poetry"* ]] ; \
	then \
		echo "Found ${POETRY_VERSION}, ok." ; \
	else \
		echo 'Please install poetry first, with e.g.:' ; \
		echo 'make install-poetry' ; \
		exit 1 ; \
	fi

install-poetry: ## install or update poetry via pip
	pip3 install -U poetry

install: check-poetry ## install via poetry
	poetry install

update: check-poetry ## Update the dependencies as according to the pyproject.toml file
	poetry update

lint: ## Run code formatters and linter
	poetry run flynt --fail-on-change --line_length=${MAX_LINE_LENGTH} bx_django_utils
	poetry run isort --check-only .
	poetry run flake8 bx_django_utils

fix-code-style: ## Fix code formatting
	poetry run flynt --line_length=${MAX_LINE_LENGTH} bx_django_utils
	poetry run autopep8 --ignore-local-config --max-line-length=${MAX_LINE_LENGTH} --aggressive --aggressive --in-place --recursive bx_django_utils
	poetry run isort .

tox-listenvs: check-poetry ## List all tox test environments
	poetry run tox --listenvs

tox: check-poetry ## Run pytest via tox with all environments
	poetry run tox

pytest: check-poetry ## Run pytest
	poetry run pytest

pytest-ci: check-poetry ## Run pytest with CI settings
	poetry run pytest -c pytest-ci.ini

test: pytest

publish: ## Release new version to PyPi
	poetry run publish

docker-test:  ## Run tests in docker
	docker build -f Dockerfile.tests .

makemessages: ## Make and compile locales message files
	./manage.sh makemessages --all --no-location --no-obsolete
	./manage.sh compilemessages --ignore=.tox

start-dev-server: ## Start Django dev. server with the test project
	./manage.sh run_testserver

clean: ## Remove created files from the test project (e.g.: SQlite, static files)
	git clean -dfX bx_django_utils_tests/

.PHONY: help install lint fix pytest publish test clean makemessages start-dev-server docker-test