from pathlib import Path

from bx_django_utils.test_utils.fixtures import BaseFixtures, fixtures_registry


EXAMPLE_FIXTURES_DATA = {'info': 'This is just a silly example...', 'foo': [1, 2, 3]}


@fixtures_registry.register()
class ExampleFixtures(BaseFixtures):
    base_path = Path(__file__).parent
    file_name = 'example_fixtures.json'

    def renew(self):
        # e.g: fetch real data from a API...
        self.store_fixture_data(data=EXAMPLE_FIXTURES_DATA)
