import copy
import logging
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from bx_django_utils.feature_flags import data_classes
from bx_django_utils.feature_flags.data_classes import FeatureFlag, State
from bx_django_utils.feature_flags.exceptions import NotUniqueFlag
from bx_django_utils.feature_flags.utils import validate_cache_key
from bx_django_utils.test_utils.cache import ClearCacheMixin


class FeatureFlagsBaseTestCase(ClearCacheMixin, TestCase):
    """"""  # noqa - Don't add to README

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.origin_registry = copy.deepcopy(FeatureFlag.registry)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        FeatureFlag.registry = cls.origin_registry


class FeatureFlagsTestCase(FeatureFlagsBaseTestCase):
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
