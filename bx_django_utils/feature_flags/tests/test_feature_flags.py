import logging
from unittest.mock import patch

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase

from bx_django_utils.feature_flags import data_classes
from bx_django_utils.feature_flags.data_classes import FeatureFlag
from bx_django_utils.feature_flags.exceptions import NotUniqueFlag
from bx_django_utils.feature_flags.state import State
from bx_django_utils.feature_flags.test_utils import FeatureFlagTestCaseMixin, get_feature_flag_db_info
from bx_django_utils.feature_flags.utils import validate_cache_key
from bx_django_utils.test_utils.assert_queries import AssertQueries


class FeatureFlagsTestCase(FeatureFlagTestCaseMixin, TestCase):
    """"""  # noqa - Don't add to README

    def setUp(self):
        super().setUp()

        FeatureFlag.registry.clear()
        self.initial_enabled_test_flag = FeatureFlag(
            cache_key='test-initial_enabled',
            human_name='A test flag that is initial "enabled"',
            initial_enabled=True,
        )
        self.initial_disabled_test_flag = FeatureFlag(
            cache_key='test-initial_disabled',
            human_name='A test flag that is initial "disabled"',
            initial_enabled=False,
        )

    def test_cache_key_validation(self):
        with self.assertRaisesMessage(ValidationError, 'cause errors if used with memcached'):
            validate_cache_key('Bam bam!')

        with self.assertRaisesMessage(ValidationError, 'cause errors if used with memcached'):
            FeatureFlag(
                cache_key='Bam bam!',
                human_name='Foo Bar',
                initial_enabled=True,
            )

    def test_uniqueness(self):
        FeatureFlag(
            cache_key='test',
            human_name='Test Uniqueness 1',
            initial_enabled=True,
        )
        with self.assertRaisesMessage(
            NotUniqueFlag, "Cache key 'feature-flags-test' already registered!"
        ):
            FeatureFlag(
                cache_key='test',
                human_name='Test Uniqueness 2',
                initial_enabled=True,
            )

    def test_basic(self):
        test_keys = {'feature-flags-test-initial_enabled', 'feature-flags-test-initial_disabled'}
        self.assertEqual(FeatureFlag.registry.keys(), test_keys)

        seen_keys = set()
        for instance in FeatureFlag.values():
            self.assertIsInstance(instance, FeatureFlag)
            seen_keys.add(instance.cache_key)
        self.assertEqual(seen_keys, test_keys)

        # Inistal state is enabled?
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.assertEqual(self.initial_enabled_test_flag.opposite_state, State.DISABLED)
        self.assertTrue(self.initial_enabled_test_flag.is_enabled)
        # Disable
        self.initial_enabled_test_flag.set_state(State.DISABLED)
        # is disabled?
        self.assertFalse(self.initial_enabled_test_flag.is_enabled)
        self.assertEqual(self.initial_enabled_test_flag.state, State.DISABLED)
        self.assertEqual(self.initial_enabled_test_flag.opposite_state, State.ENABLED)
        # enable via set_state:
        self.initial_enabled_test_flag.set_state(State.ENABLED)
        # is enabled?
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.assertEqual(self.initial_enabled_test_flag.opposite_state, State.DISABLED)
        self.assertTrue(self.initial_enabled_test_flag.is_enabled)

        # Just check the other initial state:
        self.assertEqual(self.initial_disabled_test_flag.state, State.DISABLED)
        self.assertEqual(self.initial_disabled_test_flag.opposite_state, State.ENABLED)
        self.assertFalse(self.initial_disabled_test_flag.is_enabled)

    def test_initial_state(self):
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.assertTrue(self.initial_enabled_test_flag.is_enabled)

        self.assertEqual(self.initial_disabled_test_flag.state, State.DISABLED)
        self.assertFalse(self.initial_disabled_test_flag.is_enabled)

    def test_set_state(self):
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.initial_enabled_test_flag.set_state(State.DISABLED)
        self.assertEqual(self.initial_enabled_test_flag.state, State.DISABLED)
        self.initial_enabled_test_flag.set_state(State.ENABLED)
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)

    def test_enable_disable(self):
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.initial_enabled_test_flag.disable()
        self.assertEqual(self.initial_enabled_test_flag.state, State.DISABLED)
        self.initial_enabled_test_flag.enable()
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)

    def test_redis_down(self):
        # Don't crash if "cache.get()" raise an error, e.g.: If redis is down
        self.assertTrue(self.initial_enabled_test_flag.is_enabled)
        with patch.object(
            data_classes.cache, 'get', side_effect=Exception('Cache down')
        ), self.assertLogs('bx_django_utils', level=logging.ERROR) as logs:
            self.assertTrue(self.initial_enabled_test_flag.is_enabled)

        output = '\n'.join(logs.output)
        self.assertIn(
            'Get cache key \'feature-flags-test-initial_enabled\' failed: Cache down', output
        )

    def test_cache_usage(self):
        # Test if cache works, in current test setup:
        self.assertIsNone(cache.get('foobar'))
        cache.set('foobar', 1)
        self.assertEqual(cache.get('foobar'), 1)

        # Test if FeatureFlag used the cache:
        CACHE_KEY = 'feature-flags-foo'

        # Create the flag:

        flag = FeatureFlag(cache_key='foo', human_name='foo', initial_enabled=False)
        self.assertEqual(flag.cache_key, CACHE_KEY)

        # Initializing will *not* store anything:
        self.assertIsNone(cache.get(CACHE_KEY))
        self.assertEqual(get_feature_flag_db_info(), {})

        # Fetch stage -> Store in cache + database:
        with AssertQueries() as queries:
            self.assertFalse(flag.is_enabled)  # Initial: disabled

        # First time init takes 3 queries:
        query_count = 1  # Lookup value
        query_count += 1  # create_or_update2() second lookup
        query_count += 1  # create_or_update2() insert
        queries.assert_queries(
            table_counts={'feature_flags_featureflagmodel': query_count},
            double_tables=False,
        )

        # Now it's in the cache:
        self.assertIs(cache.get(CACHE_KEY), 0)
        # ...and in the database:
        self.assertEqual(get_feature_flag_db_info(), {'feature-flags-foo': 0})

        # Check flag again should only hit the cache:
        with AssertQueries() as queries:
            self.assertFalse(flag.is_enabled)  # Still disabled?
        queries.assert_queries(table_counts={})  # No Queries made?

        # Change the flag should store the new stage in cache + database:
        with AssertQueries() as queries:
            flag.enable()
        query_count = 1  # create_or_update2() lookup
        query_count += 1  # create_or_update2() change values
        queries.assert_queries(
            table_counts={'feature_flags_featureflagmodel': query_count},
            double_tables=False,
        )
        # Changed in the cache:
        self.assertIs(cache.get(CACHE_KEY), 1)
        # ...and in the database:
        self.assertEqual(get_feature_flag_db_info(), {'feature-flags-foo': 1})

        # Query will only use the cache:
        with AssertQueries() as queries:
            self.assertTrue(flag.is_enabled)  # Now it's enabled
        queries.assert_queries(table_counts={})  # No Queries made?
