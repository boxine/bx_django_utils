from copy import deepcopy

from django.apps import apps
from django.contrib.contenttypes.models import ContentType


class ContentTypeCacheFixMixin:
    """
    TestCase mixin to fill the ContentType cache to avoid flaky database queries.

    The Problem is, that the ContentTypeManager used a shared cache for lookups.
    If your tests checks the made database queries, then you may get different results
    depending on how the cache is filled.

    With this Mixin the ContentTypeManager cache is always filled and all tests will never
    hit the databases...
    """
    @classmethod
    def _fill_content_type_cache(cls):
        # Fill ContentTypeManager cache
        app_configs = apps.get_app_configs()
        for app_config in app_configs:
            models = app_config.get_models()
            for model in models:
                ContentType.objects.get_for_model(model)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._fill_content_type_cache()
        cls._content_type_cache = deepcopy(ContentType.objects._cache)

    def setUp(self):
        super().setUp()
        ContentType.objects._cache = deepcopy(self._content_type_cache)
