from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from bx_django_utils.test_utils.content_types import ContentTypeCacheFixMixin


def assert_filled_content_type_cache():
    assert ContentType.objects._cache.keys() == {'default'}
    assert len(ContentType.objects._cache['default']) >= 20


class ContentTypesUtilsTestCase(TestCase):
    def test_fill_content_type_cache(self):
        ContentType.objects._cache.clear()

        assert len(ContentType.objects._cache) == 0

        ContentTypeCacheFixMixin._fill_content_type_cache()

        assert_filled_content_type_cache()


class ContentTypeCacheFixMixinTestCase(ContentTypeCacheFixMixin, TestCase):
    """
    Test if the cache filled for all test methods via setUp()
    """

    def test_filled_cache1(self):
        assert_filled_content_type_cache()
        ContentType.objects._cache.clear()

    def test_filled_cache2(self):
        assert_filled_content_type_cache()
        ContentType.objects._cache.clear()
