import io
import tempfile
from pathlib import Path

from bx_py_utils.test_utils.snapshot import assert_text_snapshot
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

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

    def test_renew(self):
        fixture = ExampleFixtures1()

        # Change fixtures file content:
        fixture.store_fixture_data(data=['something else!'])
        assert fixture.get_fixture_data() == ['something else!']

        # "renew" -> recreate json dump back:
        fixture.renew()

        # The "old" data?
        assert fixture.get_fixture_data() == EXAMPLE_FIXTURES_DATA1

    def test_renew_command(self):
        # Change fixtures file content:
        ExampleFixtures1().store_fixture_data(data=['something else!'])
        assert ExampleFixtures1().get_fixture_data() == ['something else!']

        # Call "renew" command:
        capture_stdout = io.StringIO()
        capture_stderr = io.StringIO()
        call_command(renew_fixtures.Command(), stdout=capture_stdout, stderr=capture_stderr)
        stdout_output = capture_stdout.getvalue()
        stderr_output = capture_stderr.getvalue()
        assert '2 Fixtures updated, ok.' in stdout_output
        assert stderr_output == ''
        assert_text_snapshot(got=stdout_output)

        assert ExampleFixtures1().get_fixture_data() == EXAMPLE_FIXTURES_DATA1

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
