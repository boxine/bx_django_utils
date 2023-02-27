import random

from django.test import TestCase

from bx_django_utils.feature_flags.data_classes import FeatureFlag
from bx_django_utils.feature_flags.test_utils import FeatureFlagTestCaseMixin, get_feature_flag_states


TEST_CACHE_KEY = 'feature-flags-test_atomic'


class FeatureFlagTestCaseMixinTestCase(FeatureFlagTestCaseMixin, TestCase):
    """"""  # noqa - Don't add to README

    @classmethod
    def setUpClass(cls):
        # "Snapshot" the current FeatureFlag.registry:
        cls.feature_flag_states = get_feature_flag_states()
        super().setUpClass()

    def _test_atomic(self):
        # No garbage entry + no "bar" entry?
        self.assertEqual(get_feature_flag_states(), self.feature_flag_states)

        # Add a new entry in FeatureFlag.registry:
        self.assertNotIn(TEST_CACHE_KEY, FeatureFlag.registry)
        bar_feature_flag = FeatureFlag(cache_key='test_atomic', human_name='bar', initial_enabled=True)
        self.assertEqual(bar_feature_flag.cache_key, TEST_CACHE_KEY)
        self.assertIn(TEST_CACHE_KEY, FeatureFlag.registry)
        self.assertTrue(bar_feature_flag.is_enabled)  # Nothing persistent?
        bar_feature_flag.disable()  # Add persistent state in cache + database
        self.assertFalse(bar_feature_flag.is_enabled)

        # Add garbage to registry -> FeatureFlagTestCaseMixin should reset it:
        FeatureFlag.registry[random.randrange(1000)] = random.randrange(1000)

    def test_atomic1(self):
        self._test_atomic()

    def test_atomic2(self):
        self._test_atomic()
