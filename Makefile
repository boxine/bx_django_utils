SHELL := /bin/bash
export DJANGO_SETTINGS_MODULE = bx_django_utils_tests.test_project.settings
export SKIP_TEST_MIGRATION = true

.PHONY: all
all: help

.PHONY: help
help:  ## List all commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9 -_]+:.*?## / {printf "\033[36m%-26s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: install
install:  ## Install via "uv" (Used system installed "uv" tool, e.g.: "pipx install uv")
	uv sync

.PHONY: update-requirements
update-requirements:  ## Update requirements
	uv lock --upgrade
	uv sync --all-extras
	uv audit
	$(MAKE) pip-audit

.PHONY: lint
lint: ## Check/fix code style by run: "ruff check --fix"
	uv run ruff check --fix

.PHONY: nox-list
nox-list:  ## List all available nox sessions
	uv run nox --list

.PHONY: nox
nox:  ## Run tests via nox with all environments and create coverage report
	uv run nox
	$(MAKE) coverage-report

.PHONY: test
test: ## Run tests
	RAISE_LOG_OUTPUT=1 ./manage.sh test --parallel --shuffle --buffer

.PHONY: coverage-report
coverage-report:  ## Creates coverage report
	uv run coverage combine --append
	uv run coverage report
	uv run coverage xml
	uv run coverage json

.PHONY: coverage
coverage:  ## Run tests with coverage (Use better "nox" target)
	uv run coverage run
	$(MAKE) coverage-report

.PHONY: update-test-snapshot-files
update-test-snapshot-files:   ## Update all snapshot files (by remove and recreate all snapshot files)
	find . -type f -name '*.snapshot.*' -delete
	RAISE_SNAPSHOT_ERRORS=0 $(MAKE) nox

.PHONY: update-test-migrations
update-test-migrations:  ## Update migration files from the test project by recreating them
	cd bx_django_utils_tests/test_app/migrations/ && find . -type f -name '00*.py' -delete
	cd bx_django_utils_tests/approve_workflow_test_app/migrations/ && find . -type f -name '00*.py' -delete
	./manage.sh makemigrations --noinput
	uv run ruff format bx_django_utils_tests/test_app/migrations/0001_initial.py
	uv run ruff format bx_django_utils_tests/approve_workflow_test_app/migrations/0001_initial.py

.PHONY: update-readme
update-readme:   ## Update README.md (will be also done in tests)
	./manage.sh update_readme

.PHONY: mypy
mypy:  ## Run mypy
	uv run mypy .

.PHONY: docker-test
docker-test:  ## Run tests in docker
	docker build --pull -f Dockerfile.tests .

.PHONY: pip-audit
pip-audit:  ## Run https://github.com/pypa/pip-audit
	uv audit  # uv audit it new: Run it in additional to pip-audit, for now
	uv export --no-header --locked --no-emit-project > /tmp/temp_requirements.txt
	uv run pip-audit --skip-editable --strict --require-hashes --disable-pip -r /tmp/temp_requirements.txt

.PHONY: publish
publish:  ## Release new version to PyPi
	uv run pip install -e .
	uv run python3 bx_django_utils_tests/publish.py

.PHONY: makemessages
makemessages: ## Make and compile locales message files
	./manage.sh makemessages --all --no-location --no-obsolete
	./manage.sh compilemessages --ignore=.nox  --ignore=.venv

.PHONY: start-dev-server
start-dev-server: ## Start Django dev. server with the test project
	$(MAKE) update-requirementsadd
	./manage.sh run_testserver

.PHONY: docker-up
docker-up: ## Start Django dev. server via Docker Compose with PostgreSQL
	$(MAKE) update-requirements
	docker compose up --build

.PHONY: docker-down
docker-down: ## Stop and remove Docker Compose containers and volumes
	docker compose down --volumes --remove-orphans

.PHONY: docker-shell-web
docker-shell-web: ## Open a shell in the running web container
	docker compose exec web /bin/bash

.PHONY: clean
clean: ## Remove created files, Docker Compose volumes and build cache
	git clean -dfX bx_django_utils_tests/
	docker compose down --volumes --remove-orphans

.PHONY: playwright-install
playwright-install: ## Install test browser for Playwright tests
	uv run playwright install chromium firefox

.PHONY: playwright-inspector
playwright-inspector:  ## Run Playwright inspector
	PWDEBUG=1 ./manage.sh test --parallel --shuffle --buffer --failfast

.PHONY: playwright-tests
playwright-tests:  ## Run only the Playwright tests
	./manage.sh test --parallel --shuffle --buffer --tag playwright

