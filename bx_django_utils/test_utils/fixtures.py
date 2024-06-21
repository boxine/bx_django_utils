"""
    Utilities to manage text fixtures in JSON files.
    A registry to collect all fixtures and a manage command to "renew" all fixtures.

    Usage, see:
     * bx_django_utils_tests/test_app/tests/fixtures/fixtures1.py
     * bx_django_utils_tests/test_app/management/commands/renew_fixtures.py
"""
import json
import os
import re
import sys
from importlib import import_module
from pathlib import Path

from bx_py_utils.path import assert_is_dir, assert_is_file
from django.apps import apps
from django.core import serializers
from django.core.management import BaseCommand
from django.core.serializers.base import DeserializedObject

from bx_django_utils.json_utils import to_json


FIXTURES_FILE_PATHS = set()


class BaseFixtures:
    """
    Base class for JSON dump fixtures.
    """

    name = None  # Will be set by registry
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

    def __repr__(self):
        return f'<Fixture:{self.name}>'


class SerializerFixtures(BaseFixtures):
    """
    Helper to store/restore model instances serialized into a JSON file.
    """

    def store_fixture_data(self, queryset):
        """
        Save the given QuerySet data into JSON fixture file
        """
        assert queryset.count() >= 1
        with Path(self.file_path).open('w') as f:
            serializers.serialize(
                format='json',
                queryset=queryset,
                indent=2,
                sort_keys=True,
                stream=f,
            )

    def create_objects(self):
        """
        Create model entries from stored JSON fixtures.
        returns the created model instance.
        """
        instances = []
        with Path(self.file_path).open('r') as f:
            for unsaved_instance in serializers.deserialize('json', f):
                assert isinstance(unsaved_instance, DeserializedObject)
                unsaved_instance.object.full_clean()
                unsaved_instance.save()
                instances.append(unsaved_instance.object)
        return instances


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
            if fixtures.name is None:
                fixtures.name = class_name

            file_path = fixtures.file_path
            if file_path in FIXTURES_FILE_PATHS:
                raise RuntimeError(f'File path "{file_path}" from "{class_name}" already used!')
            FIXTURES_FILE_PATHS.add(file_path)

            self.fixtures[class_name] = fixtures
            return FixtureClass

        return _class_wrapper

    def __iter__(self):
        yield from self.fixtures.values()

    def items(self):
        return self.fixtures.items()

    def __repr__(self):
        return f'<FixturesRegistry:{",".join(sorted(self.fixtures.keys()))}>'


fixtures_registry = FixturesRegistry()


def autodiscover(verbosity) -> int:
    """
    Register all fixtures by import all **/fixtures/**/*.py files
    """

    def get_fixtures(path):
        for root, dirs, _files in os.walk(path, followlinks=False):
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

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--filter',
            metavar='REGEX',
            help='Filter fixture class names or files by a regular expression',
        )
        parser.add_argument(
            '-a',
            '--all',
            action='store_true',
            help='Renew all fixtures and do not ask for them',
        )

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

        all_fixtures = list(fixtures_registry)

        if filter_re := options['filter']:
            filter_rex = re.compile(filter_re)
            all_fixtures = [
                fixtures
                for fixtures in all_fixtures
                if filter_rex.search(fixtures.name) or filter_rex.search(fixtures.file_name)
            ]

        if not options['all'] and len(all_fixtures) != 1:
            # Ask the user what fixtures should be updated.
            print('Please select:\n')
            fixture_map = {}
            for number, fixtures in enumerate(all_fixtures):
                fixture_map[str(number)] = fixtures
                print(f'{number:>3} - {fixtures.name} - {fixtures.file_name}')
            print('\n(ENTER nothing for renew all fixtures)')
            selection = input('Input one or more numbers seperated with spaces:')
            print()
            if not selection:
                print('Renew all fixtures:')
            else:
                all_fixtures = []
                for number in selection.split():
                    if fixture := fixture_map.get(number):
                        all_fixtures.append(fixture)
                    else:
                        print(f'Ignore: {number!r}')

                print(f'You selection: {", ".join(fixture.name for fixture in all_fixtures)}')

        no = 0
        for no, fixture in enumerate(all_fixtures, 1):
            if verbosity:
                self.stdout.write('_' * 100)
                self.stdout.write(f'{no}. renew "{fixture.name}" file "{fixture.file_path} ...')
            fixture.renew()

        if verbosity:
            self.stdout.write(f'\n{no} Fixtures updated, ok.\n')
