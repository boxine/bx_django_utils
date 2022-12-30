from django.core.cache import cache
from django.test import SimpleTestCase

from bx_django_utils.test_utils.cache import ClearCacheMixin, MockCache


class MockCacheTestCase(SimpleTestCase):
    def test_mock_cache(self):
        with MockCache() as cache_mock:
            cache.set(key='foo', value=1, timeout=123)
            cache.set(key='bar', value=2, timeout=123)
            assert cache.get(key='foo') == 1
            assert cache.get_many(keys=('foo', 'bar'), version=1) == {'foo': 1, 'bar': 2}
            assert cache_mock.raw_data == {':1:bar': 2, ':1:foo': 1}
            assert cache_mock.data == {'foo': 1, 'bar': 2}
            cache.delete(key='foo')
        assert cache_mock.data == {'bar': 2}

        with MockCache() as cache_mock:
            cache.add(key='test-add', value=1)
            cache.add(key='test-add', value=999)
        assert cache_mock.data == {'test-add': 1}

        with MockCache() as cache_mock:
            cache.set(key='test-incr', value=10)
            cache.incr(key='test-incr')  # 10+1=11
            cache.incr(key='test-incr')  # 11+1=12
            cache.decr(key='test-incr')  # 12-1=11
        assert cache_mock.raw_data == {':1:test-incr': 11}
        assert cache_mock.data == {'test-incr': 11}

        with MockCache() as cache_mock:
            assert cache.get_or_set(key='test-get-or-set', default=1) == 1
            assert cache.get_or_set(key='test-get-or-set', default=999) == 1
        assert cache_mock.raw_data == {':1:test-get-or-set': 1}
        assert cache_mock.data == {'test-get-or-set': 1}

        with MockCache() as cache_mock:
            cache.set(key='version-test', value='a', version=1)
            cache.set(key='version-test', value='b', version=2)
        assert cache_mock.raw_data == {':1:version-test': 'a', ':2:version-test': 'b'}
        assert cache_mock.data == {'version-test': 'b'}


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
