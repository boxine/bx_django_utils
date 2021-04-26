import json
import pathlib
import re
from unittest import TestCase

from bx_py_utils.graphql_introspection import complete_query, introspection_query
from bx_py_utils.test_utils.snapshot import assert_text_snapshot


TEST_DIR = pathlib.Path(__file__).parent / 'graphql_introspection'


class GraphQLIntrospectionTest(TestCase):
    def test_introspection_query(self):
        assert_text_snapshot(TEST_DIR, 'graphql_introspection_query', introspection_query(3))

    def _craft_query_snapshot(self, test_name, root_name, allow_recursive=True):
        with (TEST_DIR / f'{test_name}.json').open() as f:
            introspection_doc = json.load(f)['data']

        got = complete_query(introspection_doc, root_name, allow_recursive=allow_recursive)
        assert_text_snapshot(TEST_DIR, test_name, got)

    def test_craft_query_string_toniecloud_config(self):
        self._craft_query_snapshot('toniecloud_config', 'Query')

    def test_craft_query_string_toniecloud_complete(self):
        self._craft_query_snapshot('toniecloud_complete', 'Query')

    def test_craft_query_string_shopify(self):
        self._craft_query_snapshot('shopify_schema', 'QueryRoot', allow_recursive=False)

    def test_craft_query_string_shopify_product_only(self):
        with (TEST_DIR / f'shopify_schema.json').open() as f:
            introspection_doc = json.load(f)['data']

        got = complete_query(introspection_doc, 'Product')
        assert_text_snapshot(TEST_DIR, 'shopify_product_only', got)

        depth2 = complete_query(introspection_doc, 'Product', max_depth=2)
        assert_text_snapshot(TEST_DIR, 'shopify_product_only_depth2', depth2)
