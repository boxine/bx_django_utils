from copy import deepcopy

from bx_django_utils.feature_flags.data_classes import FeatureFlag
from bx_django_utils.test_utils.cache import ClearCacheMixin


def get_feature_flag_states() -> dict:
    """
    Collects information about all registered feature flags and their current state.
    If FeatureFlagTestCaseMixin used -> the current state is the initial state!
    """
    return {feature_flag.cache_key: feature_flag.is_enabled for feature_flag in FeatureFlag.values()}


class FeatureFlagTestCaseMixin(ClearCacheMixin):
    """
    Mixin for `TestCase` that will change `FeatureFlag` entries. To make the tests atomic.

    * Restore `FeatureFlag.registry` between tests.
    * Restore all feature flags to the initial stage between tests.

    Used ClearCacheMixin to remove persistent data in Django's cache.
    Should be used with django.test.TestCase so that persistent data in database also be removed!
    """

    @classmethod
    def setUpClass(cls):
        cls._origin_feature_flag_registry = FeatureFlag.registry
        super().setUpClass()

    def setUp(self):
        super().setUp()
        FeatureFlag.registry = deepcopy(self._origin_feature_flag_registry)

    def tearDown(self):
        super().tearDown()
        FeatureFlag.registry = self._origin_feature_flag_registry
