import tempfile
from pathlib import Path
from unittest.mock import patch

from bx_py_utils.test_utils.redirect import RedirectOut
from bx_py_utils.test_utils.snapshot import assert_text_snapshot
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from bx_django_utils.test_utils import fixtures
from bx_django_utils.test_utils.fixtures import (
    FIXTURES_FILE_PATHS,
    BaseFixtures,
    FixturesRegistry,
    SerializerFixtures,
    fixtures_registry,
)
from bx_django_utils_tests.test_app.management.commands import renew_fixtures
from bx_django_utils_tests.test_app.models import ColorFieldTestModel
from bx_django_utils_tests.test_app.tests.fixtures.fixtures1 import (
    EXAMPLE_FIXTURES_DATA1,
    EXAMPLE_FIXTURES_DATA2,
    ExampleFixtures1,
    ExampleFixtures2,
)


class FixturesHelperTestCase(SimpleTestCase):
    def reset(self):
        FIXTURES_FILE_PATHS.clear()

    def setUp(self):
        super().setUp()
        self.reset()

    def tearDown(self):
        super().tearDown()
        self.reset()

    def test_example_fixtures(self):
        assert ExampleFixtures1().get_fixture_data() == EXAMPLE_FIXTURES_DATA1
        assert ExampleFixtures2().get_fixture_data() == EXAMPLE_FIXTURES_DATA2

    def test_registry(self):
        assert sorted(fixtures_registry.fixtures.keys()) == ['ExampleFixtures1', 'ExampleFixtures2']

    def test_str_repr(self):
        self.assertEqual(
            repr(fixtures_registry),
            '<FixturesRegistry:ExampleFixtures1,ExampleFixtures2>',
        )
        self.assertEqual(
            str(fixtures_registry),
            '<FixturesRegistry:ExampleFixtures1,ExampleFixtures2>',
        )

        fixtures = next(iter(fixtures_registry))
        self.assertIsInstance(fixtures, BaseFixtures)
        self.assertEqual(repr(fixtures), '<Fixture:ExampleFixtures1>')
        self.assertEqual(str(fixtures), '<Fixture:ExampleFixtures1>')

    def test_renew(self):
        fixture = ExampleFixtures1()

        # Change fixtures file content:
        fixture.store_fixture_data(data=['something else!'])
        assert fixture.get_fixture_data() == ['something else!']

        # "renew" -> recreate json dump back:
        fixture.renew()

        # The "old" data?
        assert fixture.get_fixture_data() == EXAMPLE_FIXTURES_DATA1

    def test_overwriting(self):
        class Foo(BaseFixtures):
            base_path = Path(__file__).parent
            file_name = 'bar.json'

        class Bar(Foo):
            pass

        registry = FixturesRegistry()
        registry.register()(Foo)

        # It's not possible to register more than two times:
        with self.assertRaisesMessage(RuntimeError, 'Fixture class "Foo" already registered!'):
            registry.register()(Foo)

        foo = registry.fixtures['Foo']
        file_path = foo.file_path

        # It's not possible to overwrite the same JSON file:
        with self.assertRaisesMessage(
            RuntimeError, f'File path "{file_path}" from "Bar" already used!'
        ):
            registry.register()(Bar)


class SerializerFixturesTestCase(TestCase):
    def test_basic(self):
        with tempfile.NamedTemporaryFile(prefix='serializer_fixtures_', suffix='.json') as tmp_file:
            tmp_file_path = Path(tmp_file.name)

            class Example(SerializerFixtures):
                """Just a test example implementation"""

                base_path = tmp_file_path.parent
                file_name = tmp_file_path.name

                def renew(self):
                    ColorFieldTestModel.objects.create(pk=1, required_color='#00AAff')
                    qs = ColorFieldTestModel.objects.all()
                    self.store_fixture_data(queryset=qs)

            example = Example()

            # Store the model instance into the JSON file:
            example.renew()

            json_str = tmp_file_path.read_text()
            self.assertIn('#00AAff', json_str)

            ColorFieldTestModel.objects.all().delete()
            self.assertEqual(ColorFieldTestModel.objects.count(), 0)

            # Maybe useful: It's possible to get the serializer data:
            data = example.get_fixture_data()
            self.assertEqual(
                data,
                [
                    {
                        'fields': {'optional_color': None, 'required_color': '#00AAff'},
                        'model': 'test_app.colorfieldtestmodel',
                        'pk': 1,
                    }
                ],
            )

            # Recreate the objects:
            instances = example.create_objects()
            self.assertEqual(ColorFieldTestModel.objects.count(), 1)
            created_instance = ColorFieldTestModel.objects.first()
            self.assertEqual(instances, [created_instance])


class FixtureMock(BaseFixtures):
    def __init__(self, name):
        self.name = name
        self.file_name = f'{name}.json'
        self.file_path = Path(f'/path/to/{name}.json')

    def renew(self):
        print(f'Mocked renew "{self.name}"')


class RegistryMock(FixturesRegistry):
    def __init__(self):
        self.fixtures = {
            'fixture1': FixtureMock('fixture1'),
            'fixture2': FixtureMock('fixture2'),
            'fixture3': FixtureMock('fixture3'),
        }


class InputMock:
    def __init__(self, input):
        self.input = input

    def __call__(self, text):
        print(text, self.input)
        return self.input


class RenewAllFixturesBaseCommandTestCase(SimpleTestCase):
    def call_command(
        self,
        *,
        options=None,
        expected_stdout: str | list[str],
        expected_stderr='',
        strip_output=True,
        input=None,
    ):
        if options is None:
            options = {}
        reg_mock = RegistryMock()
        input_mock = InputMock(input)
        with patch.object(fixtures, 'fixtures_registry', reg_mock), patch.object(fixtures, 'input', input_mock):
            with RedirectOut(strip=strip_output) as buffer:
                call_command(
                    renew_fixtures.Command(),
                    stdout=buffer._stdout_buffer,
                    stderr=buffer._stderr_buffer,
                    **options,
                )
            stderr_output = buffer.stderr
            stdout_output = buffer.stdout
            try:
                self.assertEqual(stderr_output, expected_stderr)

                if isinstance(expected_stdout, list):
                    for part in expected_stdout:
                        self.assertIn(part, stdout_output)
                else:
                    self.assertEqual(stdout_output, expected_stdout)
            except AssertionError:
                print('=' * 100)
                print('stdout:')
                print('-' * 100)
                print(stdout_output)
                print('-' * 100)
                print('stderr:')
                print('-' * 100)
                print(stderr_output)
                print('=' * 100)
                raise
        return stdout_output

    def test_renew_all(self):
        stdout_output = self.call_command(
            options=dict(all=True),
            expected_stdout=[
                '1. renew "fixture1" file "/path/to/fixture1.json ...',
                'Mocked renew "fixture1"',
                '2. renew "fixture2" file "/path/to/fixture2.json ...',
                'Mocked renew "fixture2"',
                '3. renew "fixture3" file "/path/to/fixture3.json ...',
                'Mocked renew "fixture3"',
                '3 Fixtures updated, ok.',
            ],
        )
        assert_text_snapshot(got=stdout_output)

    def test_renew_all_with_regex(self):
        stdout_output = self.call_command(
            options=dict(all=True, filter='fixture2'),
            expected_stdout=[
                '1. renew "fixture2" file "/path/to/fixture2.json ...',
                'Mocked renew "fixture2"',
                '1 Fixtures updated, ok.',
            ],
        )
        assert_text_snapshot(got=stdout_output)

    def test_select_fixtures(self):
        # Select only a few:
        stdout_output = self.call_command(
            expected_stdout=[
                '0 - fixture1 - fixture1.json',
                '1 - fixture2 - fixture2.json',
                '2 - fixture3 - fixture3.json',
                'Input one or more numbers seperated with spaces: 1 2',
                'You selection: fixture2, fixture3',
                '1. renew "fixture2" file "/path/to/fixture2.json ...',
                'Mocked renew "fixture2"',
                '2. renew "fixture3" file "/path/to/fixture3.json ...',
                'Mocked renew "fixture3"',
                '2 Fixtures updated, ok.',
            ],
            input='1 2',
        )
        assert_text_snapshot(got=stdout_output)

        # Select all by hit ENTER:
        stdout_output = self.call_command(
            expected_stdout=[
                'Renew all fixtures:',
                '3 Fixtures updated, ok.',
            ],
            input='',
        )
        assert_text_snapshot(got=stdout_output)
