from django.core.cache import cache
from django.test import SimpleTestCase

from bx_django_utils.test_utils.cache import ClearCacheMixin, MockCache


def test_mock_cache():
    with MockCache() as cache_mock:
        cache.set(key='foo', value=1, timeout=123)
        cache.set(key='bar', value=2, timeout=123)
        assert cache.get(key='foo') == 1
        assert cache_mock.data == {'foo': 1, 'bar': 2}
        cache.delete(key='foo')
    assert cache_mock.data == {'bar': 2}


class ClearCacheTestCase(ClearCacheMixin, SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.set(key='foo', value=1, timeout=0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.set(key='foo', value=2, timeout=0)

    def setUp(self):
        super().setUp()
        assert cache.get(key='foo') is None

    def tearDown(self):
        super().tearDown()
        assert cache.get(key='foo') is None

    def test_check1(self):
        assert cache.get(key='foo') is None
        cache.set(key='foo', value=3, timeout=0)

    def test_check2(self):
        assert cache.get(key='foo') is None
        cache.set(key='foo', value=4, timeout=0)
