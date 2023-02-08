SHELL := /bin/bash
MAX_LINE_LENGTH := 119
export DJANGO_SETTINGS_MODULE = bx_django_utils_tests.test_project.settings
export SKIP_TEST_MIGRATION = true

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

install-poetry: ## install poetry
	curl -sSL https://install.python-poetry.org | python3 -

install: check-poetry ## install via poetry
	python3 -m venv .venv
	poetry install

update: check-poetry ## Update the dependencies as according to the pyproject.toml file
	poetry update

lint: ## Run code formatters and linter
	poetry run darker --diff --check
	poetry run isort --check-only .
	poetry run flake8 .

fix-code-style: ## Fix code formatting
	poetry run darker
	poetry run isort .

tox-listenvs: check-poetry ## List all tox test environments
	poetry run tox --listenvs

tox: check-poetry ## Run unittests via tox with all environments
	poetry run tox

test: check-poetry  ## Run unittests
	RAISE_LOG_OUTPUT=1 ./manage.sh test --parallel --shuffle --buffer

coverage_test: ## Run tests and generate coverage html report
	poetry run coverage run --rcfile=pyproject.toml manage.py test --parallel --shuffle
	poetry run coverage html
	poetry run coverage report

update-test-snapshot-files:   ## Update all snapshot files (by remove and recreate all snapshot files)
	find . -type f -name '*.snapshot.*' -delete
	RAISE_SNAPSHOT_ERRORS=0 ./manage.sh test --parallel

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
