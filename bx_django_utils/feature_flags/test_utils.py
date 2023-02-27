from copy import deepcopy

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings

from bx_django_utils.feature_flags.data_classes import FeatureFlag
from bx_django_utils.feature_flags.models import FeatureFlagModel
from bx_django_utils.test_utils.cache import ClearCacheMixin


def get_feature_flag_states() -> dict:
    """
    Collects information about all registered feature flags and their current state.
    If FeatureFlagTestCaseMixin used -> the current state is the initial state!
    """
    return {feature_flag.cache_key: feature_flag.is_enabled for feature_flag in FeatureFlag.values()}


def get_feature_flag_cache_info() -> dict:
    # Not in README: Probably only useful for internal use.
    result = {}
    for cache_key in sorted(FeatureFlag.registry.keys()):
        state = cache.get(cache_key)
        if state is not None:
            result[cache_key] = state
    return result


def get_feature_flag_db_info() -> dict:
    # Not in README: Probably only useful for internal use.
    return dict(FeatureFlagModel.objects.order_by('cache_key').values_list('cache_key', 'state'))


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

        # Use per-process and thread-safe cache backend for tests.
        # This is important if tests run with `--parallel`
        caches_settings = deepcopy(settings.CACHES)
        caches_settings['default'] = {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
        cls._overwrite_cache = override_settings(CACHES=caches_settings)
        cls._overwrite_cache.__enter__()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._overwrite_cache.__exit__(None, None, None)

    def setUp(self):
        super().setUp()
        FeatureFlag.registry = deepcopy(self._origin_feature_flag_registry)

    def tearDown(self):
        super().tearDown()
        FeatureFlag.registry = self._origin_feature_flag_registry
