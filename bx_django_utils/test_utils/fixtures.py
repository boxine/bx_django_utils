"""
    Utilities to manage text fixtures in JSON files.
    A registry to collect all fixtures and a manage command to "renew" all fixtures.

    Usage, see:
     * bx_django_utils_tests/test_app/tests/fixtures/fixtures1.py
     * bx_django_utils_tests/test_app/management/commands/renew_fixtures.py
"""
import json
import os
import sys
from importlib import import_module
from pathlib import Path

from bx_py_utils.path import assert_is_dir, assert_is_file
from django.apps import apps
from django.core.management import BaseCommand

from bx_django_utils.json_utils import to_json


FIXTURES_FILE_PATHS = set()


class BaseFixtures:
    """
    Base class for JSON dump fixtures.
    """

    base_path = None
    file_name = None

    def __init__(self):
        assert self.base_path, 'No base_path defined!'
        assert self.file_name, 'No file_name defined!'
        assert self.file_name.endswith('.json'), f'File extension not ".json": {self.file_name!r}'
        assert_is_dir(self.base_path)
        self.file_path = self.base_path / self.file_name

    def get_fixture_data(self):
        try:
            assert_is_file(self.file_path)
        except OSError as err:
            raise OSError(f'{err} (Hint: renew test fixtures!)')
        with Path(self.file_path).open('r') as f:
            return json.load(f)

    def store_fixture_data(self, data):
        assert data, 'Given data is empty!'
        with Path(self.file_path).open('w') as f:
            f.write(to_json(data, indent=2))

    def renew(self):
        """
        Endpoint to update the existing fixture data.
        Should be use self.store_fixture_data()
        """
        raise NotImplementedError


class FixturesRegistry:
    """
    Registry to collect a list of all existing fixture classes.
    """

    def __init__(self):
        self.fixtures = {}

    def register(self):
        def _class_wrapper(FixtureClass):
            assert issubclass(FixtureClass, BaseFixtures)

            class_name = FixtureClass.__name__

            if class_name in self.fixtures:
                raise RuntimeError(f'Fixture class "{class_name}" already registered!')

            fixtures = FixtureClass()
            file_path = fixtures.file_path
            if file_path in FIXTURES_FILE_PATHS:
                raise RuntimeError(f'File path "{file_path}" from "{class_name}" already used!')
            FIXTURES_FILE_PATHS.add(file_path)

            self.fixtures[class_name] = fixtures
            return FixtureClass

        return _class_wrapper

    def __iter__(self):
        for class_name, fixtures in self.fixtures.items():
            yield fixtures


fixtures_registry = FixturesRegistry()


def autodiscover(verbosity) -> int:
    """
    Register all fixtures by import all **/fixtures/**/*.py files
    """

    def get_fixtures(path):
        for root, dirs, files in os.walk(path, followlinks=False):
            if 'fixtures' in dirs:
                yield from Path(root, 'fixtures').glob('**/*.py')

    count = 0
    for app_config in apps.get_app_configs():
        path = app_config.path

        for fixtures_path in get_fixtures(path):
            rel_path = fixtures_path.relative_to(path)
            parts = rel_path.with_suffix('').parts
            rel_pkg = '.'.join(parts)
            full_pkg = f'{app_config.name}.{rel_pkg}'
            if verbosity > 1:
                print(f'Fixtures found: {full_pkg!r}')
            import_module(full_pkg)
            count += 1
    return count


class RenewAllFixturesBaseCommand(BaseCommand):
    """
    A base Django manage command to renew all existing fixture JSON dump files
    """

    help = 'Renew all (example) test fixtures'

    def handle(self, *args, **options):
        verbosity = options['verbosity']

        count = autodiscover(verbosity)  # fill registry by import all fixture files
        if verbosity:
            self.stdout.write(f'Found {count} fixtures files.')

        if count < 1:
            self.stderr.write('No fixtures files found in all installed Django apps!')
            sys.exit(1)

        if not fixtures_registry.fixtures:
            self.stderr.write('No fixtures class registered!')
            sys.exit(1)

        no = 0
        for no, fixture in enumerate(fixtures_registry, 1):
            if verbosity:
                self.stdout.write('_' * 100)
                self.stdout.write(
                    f'{no}. renew "{fixture.__class__.__name__}" file "{fixture.file_name}...'
                )
            fixture.renew()

        if verbosity:
            self.stdout.write(f'\n{no} Fixtures updated, ok.\n')
