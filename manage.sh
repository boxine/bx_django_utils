#!/bin/sh

(
    set -ex
    .venv/bin/python --version
    .venv/bin/django-admin --version
)

exec .venv/bin/python3 manage.py "$@"
