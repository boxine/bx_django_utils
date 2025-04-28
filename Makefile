SHELL := /bin/bash
export DJANGO_SETTINGS_MODULE = bx_django_utils_tests.test_project.settings
export SKIP_TEST_MIGRATION = true
export PATH := .venv/bin:$(PATH)

.PHONY: all
all: help

.PHONY: help
help:  ## List all commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9 -_]+:.*?## / {printf "\033[36m%-26s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: install-base-req
install-base-req:  ## Install needed base packages via apt
	sudo apt install python3-pip python3-venv

.PHONY: install
install:  ## Install the project in a Python virtualenv
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -U uv
	.venv/bin/uv sync

.PHONY: update-requirements
update-requirements:  ## Update requirements
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -U uv
	.venv/bin/uv lock --upgrade
	.venv/bin/uv sync
	$(MAKE) pip-audit

.PHONY: lint
lint: ## Run code formatters and linter
	.venv/bin/darker --diff --check
	.venv/bin/flake8 .

.PHONY: fix-code-style
fix-code-style: ## Fix code formatting
	.venv/bin/darker
	.venv/bin/flake8 .

.PHONY: nox-list
nox-list:  ## List all available nox sessions
	.venv/bin/nox --list

.PHONY: nox
nox:  ## Run tests via nox with all environments
	.venv/bin/nox
	$(MAKE) coverage-report

.PHONY: test
test: ## Run tests
	RAISE_LOG_OUTPUT=1 ./manage.sh test --parallel --shuffle --buffer

.PHONY: coverage-report
coverage-report:  ## Creates coverage report
	.venv/bin/coverage combine --append
	.venv/bin/coverage report
	.venv/bin/coverage xml
	.venv/bin/coverage json

.PHONY: coverage
coverage:  ## Run tests with coverage
	.venv/bin/coverage run
	$(MAKE) coverage-report

.PHONY: update-test-snapshot-files
update-test-snapshot-files:   ## Update all snapshot files (by remove and recreate all snapshot files)
	find . -type f -name '*.snapshot.*' -delete
	RAISE_SNAPSHOT_ERRORS=0 $(MAKE) nox

.PHONY: update-test-migrations
update-test-migrations:  ## Update migration files from the test project
	cd bx_django_utils_tests/test_app/migrations/ && find . -type f -name '00*.py' -delete
	cd bx_django_utils_tests/approve_workflow_test_app/migrations/ && find . -type f -name '00*.py' -delete
	./manage.sh makemigrations --noinput
	.venv/bin/black bx_django_utils_tests/test_app/migrations/0001_initial.py
	.venv/bin/isort bx_django_utils_tests/test_app/migrations/0001_initial.py
	.venv/bin/black bx_django_utils_tests/approve_workflow_test_app/migrations/0001_initial.py
	.venv/bin/isort bx_django_utils_tests/approve_workflow_test_app/migrations/0001_initial.py

.PHONY: mypy
mypy:  ## Run mypy
	.venv/bin/mypy .

.PHONY: docker-test
docker-test:  ## Run tests in docker
	docker build --pull -f Dockerfile.tests .

.PHONY: pip-audit
pip-audit:  ## Run https://github.com/pypa/pip-audit
	.venv/bin/uv export --no-header --frozen --no-editable --no-emit-project -o /tmp/temp_requirements.txt
	.venv/bin/pip-audit --strict --require-hashes --disable-pip -r /tmp/temp_requirements.txt

.PHONY: publish
publish:  ## Release new version to PyPi
	.venv/bin/pip install -e .
	.venv/bin/python bx_django_utils_tests/test_project/publish.py

.PHONY: makemessages
makemessages: ## Make and compile locales message files
	./manage.sh makemessages --all --no-location --no-obsolete
	./manage.sh compilemessages --ignore=.nox

.PHONY: start-dev-server
start-dev-server: ## Start Django dev. server with the test project
	./manage.sh run_testserver

.PHONY: clean
clean: ## Remove created files from the test project (e.g.: SQlite, static files)
	git clean -dfX bx_django_utils_tests/

.PHONY: playwright-install
playwright-install: ## Install test browser for Playwright tests
	.venv/bin/playwright install chromium firefox

.PHONY: playwright-inspector
playwright-inspector:  ## Run Playwright inspector
	PWDEBUG=1 ./manage.sh test --parallel --shuffle --buffer --failfast

.PHONY: playwright-tests
playwright-tests:  ## Run only the Playwright tests
	./manage.sh test --parallel --shuffle --buffer --tag playwright