from pathlib import Path

from bx_django_utils.test_utils.fixtures import BaseFixtures, fixtures_registry


EXAMPLE_FIXTURES_DATA1 = {'info': 'This is just a silly example...', 'foo': [1, 2, 3]}
EXAMPLE_FIXTURES_DATA2 = ['Something Different', 'Test Fixtures']


BASE_PATH = Path(__file__).parent


@fixtures_registry.register()
class ExampleFixtures1(BaseFixtures):
    base_path = BASE_PATH
    file_name = 'example_fixtures1.json'

    def renew(self):
        # e.g: fetch real data from a API...
        self.store_fixture_data(data=EXAMPLE_FIXTURES_DATA1)


@fixtures_registry.register()
class ExampleFixtures2(BaseFixtures):
    base_path = BASE_PATH
    file_name = 'example_fixtures2.json'

    def renew(self):
        # e.g: fetch real data from a API...
        self.store_fixture_data(data=EXAMPLE_FIXTURES_DATA2)
