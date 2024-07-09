SHELL := /bin/bash
export DJANGO_SETTINGS_MODULE = bx_django_utils_tests.test_project.settings
export SKIP_TEST_MIGRATION = true

all: help

help:  ## List all commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9 -_]+:.*?## / {printf "\033[36m%-26s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install-base-req:  ## Install needed base packages via apt
	sudo apt install python3-pip python3-venv

install:  ## Install the project in a Python virtualenv
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -U pipenv
	.venv/bin/pipenv install --dev
	.venv/bin/pip install -e .

update-requirements:  ## Update requirements
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -U pipenv
	.venv/bin/pipenv update --dev

lint: ## Run code formatters and linter
	.venv/bin/pipenv run darker --diff --check
	.venv/bin/pipenv run flake8 .

fix-code-style: ## Fix code formatting
	.venv/bin/pipenv run darker

tox-listenvs:  ## List all tox test environments
	.venv/bin/tox --listenvs

tox:  ## Run tests via tox with all environments
	.venv/bin/tox

test: ## Run tests
	RAISE_LOG_OUTPUT=1 ./manage.sh test --parallel --shuffle --buffer

coverage:  ## Run tests with coverage
	.venv/bin/coverage run
	.venv/bin/coverage combine --append
	.venv/bin/coverage report
	.venv/bin/coverage xml
	.venv/bin/coverage json

update-test-snapshot-files:   ## Update all snapshot files (by remove and recreate all snapshot files)
	find . -type f -name '*.snapshot.*' -delete
	RAISE_SNAPSHOT_ERRORS=0 .venv/bin/python -m unittest

update-test-migrations:  ## Update migration files from the test project
	cd bx_django_utils_tests/test_app/migrations/ && find . -type f -name '00*.py' -delete
	cd bx_django_utils_tests/approve_workflow_test_app/migrations/ && find . -type f -name '00*.py' -delete
	./manage.sh makemigrations --noinput
	.venv/bin/black bx_django_utils_tests/test_app/migrations/0001_initial.py
	.venv/bin/isort bx_django_utils_tests/test_app/migrations/0001_initial.py
	.venv/bin/black bx_django_utils_tests/approve_workflow_test_app/migrations/0001_initial.py
	.venv/bin/isort bx_django_utils_tests/approve_workflow_test_app/migrations/0001_initial.py

mypy:  ## Run mypy
	.venv/bin/mypy .

docker-test:  ## Run tests in docker
	docker build --pull -f Dockerfile.tests .

safety:  ## Run https://github.com/pyupio/safety
	.venv/bin/safety check --full-report

publish:  ## Release new version to PyPi
	.venv/bin/pip install -e .
	.venv/bin/pipenv run python bx_django_utils_tests/test_project/publish.py

makemessages: ## Make and compile locales message files
	./manage.sh makemessages --all --no-location --no-obsolete
	./manage.sh compilemessages --ignore=.tox

start-dev-server: ## Start Django dev. server with the test project
	./manage.sh run_testserver

clean: ## Remove created files from the test project (e.g.: SQlite, static files)
	git clean -dfX bx_django_utils_tests/

playwright-install: ## Install test browser for Playwright tests
	.venv/bin/playwright install chromium firefox

playwright-inspector:  ## Run Playwright inspector
	PWDEBUG=1 ./manage.sh test --parallel --shuffle --buffer --failfast

playwright-tests:  ## Run only the Playwright tests
	./manage.sh test --parallel --shuffle --buffer --tag playwright

.PHONY: help install lint fix publish test clean makemessages start-dev-server docker-test playwright-install playwright-inspector playwright-tests
