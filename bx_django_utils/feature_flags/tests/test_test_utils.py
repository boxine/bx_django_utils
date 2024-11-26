import random

from django.test import TestCase

from bx_django_utils.feature_flags.data_classes import FeatureFlag
from bx_django_utils.feature_flags.test_utils import FeatureFlagTestCaseMixin, get_feature_flag_db_info

TEST_CACHE_KEY = 'feature-flags-test_atomic'


class FeatureFlagTestCaseMixinTestCase(FeatureFlagTestCaseMixin, TestCase):
    """"""  # noqa - Don't add to README

    warum_up_feature_flag_cache = False

    def _test_atomic(self):
        # We always start fresh: Only with existing entries:
        self.assertEqual(FeatureFlag.registry.keys(), {'feature-flags-foo', 'feature-flags-bar'})

        # DB empty? (No warp-up made in mixin)
        self.assertEqual(get_feature_flag_db_info(), {})

        # Add a new "test_atomic" entry in FeatureFlag.registry:
        self.assertNotIn(TEST_CACHE_KEY, FeatureFlag.registry)
        bar_feature_flag = FeatureFlag(cache_key='test_atomic', human_name='bar', initial_enabled=True)
        self.assertEqual(bar_feature_flag.cache_key, TEST_CACHE_KEY)
        self.assertIn(TEST_CACHE_KEY, FeatureFlag.registry)
        self.assertTrue(bar_feature_flag.is_enabled)  # Nothing persistent?
        bar_feature_flag.disable()  # Add persistent state in cache + database
        self.assertFalse(bar_feature_flag.is_enabled)

        # Only our "test_atomic" stored?
        self.assertEqual(get_feature_flag_db_info(), {'feature-flags-test_atomic': 0})

        # Add garbage to registry -> FeatureFlagTestCaseMixin should reset it:
        FeatureFlag.registry[random.randrange(1000)] = random.randrange(1000)

    def test_atomic1(self):
        self._test_atomic()

    def test_atomic2(self):
        self._test_atomic()


class FeatureFlagTestCaseMixinTestCase1(FeatureFlagTestCaseMixin, TestCase):
    """"""  # noqa - Don't add to README

    warum_up_feature_flag_cache = True

    def test_warm_up(self):
        self.assertEqual(get_feature_flag_db_info(), {'feature-flags-bar': 0, 'feature-flags-foo': 1})
