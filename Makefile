SHELL := /bin/bash
export DJANGO_SETTINGS_MODULE = bx_django_utils_tests.test_project.settings
export SKIP_TEST_MIGRATION = true

all: help

help: ## List all commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9 -]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check-poetry:
	@if [[ "$(shell poetry --version 2>/dev/null)" == *"Poetry"* ]] ; \
	then \
		echo "Poetry found, ok." ; \
	else \
		echo 'Please install poetry first, with e.g.:' ; \
		echo 'make install-poetry' ; \
		exit 1 ; \
	fi

install-base-req:  ## Install needed base packages via apt
	sudo apt install python3-pip python3-venv

install-poetry: ## install poetry
	curl -sSL https://install.python-poetry.org | python3 -

install: check-poetry ## install via poetry
	python3 -m venv .venv
	poetry install

update: check-poetry ## Update the dependencies as according to the pyproject.toml file
	python3 -m venv .venv
	poetry self update
	poetry update -v
	poetry install

clear-partial-coverage:
	rm -f .coverage.*

lint: ## Run code formatters and linter
	poetry run darker --diff --check
	poetry run isort --check-only .
	poetry run flake8 .

fix-code-style: ## Fix code formatting
	poetry run darker
	poetry run isort .

tox-listenvs: check-poetry ## List all tox test environments
	poetry run tox --listenvs

tox: check-poetry clear-partial-coverage ## Run unittests via tox with all environments
	poetry run tox p
	poetry run coverage combine
	poetry run coverage html
	poetry run coverage report

test: check-poetry  ## Run unittests
	RAISE_LOG_OUTPUT=1 ./manage.sh test --parallel --shuffle --buffer

coverage_test: clear-partial-coverage ## Run tests and generate coverage html report
	poetry run coverage run --parallel-mode manage.py test --parallel --shuffle
	poetry run coverage combine
	poetry run coverage html
	poetry run coverage report

update-test-snapshot-files:   ## Update all snapshot files (by remove and recreate all snapshot files)
	find . -type f -name '*.snapshot.*' -delete
	RAISE_SNAPSHOT_ERRORS=0 $(MAKE) tox

update-test-migrations:  ## Update migration files from the test project
	cd bx_django_utils_tests/test_app/migrations/ && find . -type f -name '00*.py' -delete
	cd bx_django_utils_tests/approve_workflow_test_app/migrations/ && find . -type f -name '00*.py' -delete
	./manage.sh makemigrations --noinput
	poetry run black bx_django_utils_tests/test_app/migrations/0001_initial.py
	poetry run isort bx_django_utils_tests/test_app/migrations/0001_initial.py
	poetry run black bx_django_utils_tests/approve_workflow_test_app/migrations/0001_initial.py
	poetry run isort bx_django_utils_tests/approve_workflow_test_app/migrations/0001_initial.py

publish: install  ## Release new version to PyPi
	poetry run publish

docker-test:  ## Run tests in docker
	docker build --pull -f Dockerfile.tests .

makemessages: ## Make and compile locales message files
	./manage.sh makemessages --all --no-location --no-obsolete
	./manage.sh compilemessages --ignore=.tox

start-dev-server: ## Start Django dev. server with the test project
	./manage.sh run_testserver

clean: ## Remove created files from the test project (e.g.: SQlite, static files)
	git clean -dfX bx_django_utils_tests/

playwright-install: ## Install test browser for Playwright tests
	poetry run playwright install chromium firefox

playwright-inspector:  ## Run Playwright inspector
	PWDEBUG=1 ./manage.sh test --parallel --shuffle --buffer --failfast

playwright-tests:  ## Run only the Playwright tests
	./manage.sh test --parallel --shuffle --buffer --tag playwright

.PHONY: help install lint fix publish test clean makemessages start-dev-server docker-test playwright-install playwright-inspector playwright-tests
