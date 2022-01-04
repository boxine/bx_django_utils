import inspect
import pickle
from collections import OrderedDict
from threading import Lock
from unittest import mock

from django.core.cache import cache
from django.core.cache.backends.base import default_key_func
from django.core.cache.backends.locmem import LocMemCache


class FakeCache(LocMemCache):

    def __init__(self):
        # BaseCache attributes:
        self.default_timeout = None
        self._max_entries = 300
        self._cull_frequency = 3
        self.key_prefix = ''
        self.version = 1
        self.key_func = default_key_func

        # LocMemCache attributes:
        self._cache = OrderedDict()
        self._expire_info = {}
        self._lock = Lock()

        # Storage for 'clean' cache data, without version:
        self.data = {}

    def add(self, key, value, **kwargs):
        if key not in self.data:
            self.data[key] = value
        return super().add(key, value, **kwargs)

    def set(self, key, value, **kwargs):
        self.data[key] = value
        return super().set(key, value, **kwargs)

    def delete(self, key, **kwargs):
        if key in self.data:
            del self.data[key]
        return super().delete(key, **kwargs)

    def incr(self, key, *args, **kwargs):
        new_value = super().incr(key, *args, **kwargs)
        self.data[key] = new_value
        return new_value

    def clear(self):
        self.data.clear()
        super().clear()


class MockCache:
    """
    Mock Django cache backend, so it's easy to check/manipulate the cache content
    """

    def __init__(self):
        self.fake_cache = FakeCache()

        self.mocks = []
        methods = inspect.getmembers(self.fake_cache, inspect.ismethod)
        for name, func in methods:
            if name.startswith('_'):
                continue

            self.mocks.append(
                mock.patch(f'django.core.cache.cache.{name}', func)
            )

    @property
    def data(self):
        """
        :return: "cleaned" cache data, without version
        """
        return self.fake_cache.data

    @property
    def raw_data(self):
        """
        :return: cache data with all versions
        """
        return {
            key: pickle.loads(pickled)
            for key, pickled in self.fake_cache._cache.items()
        }

    def __enter__(self):
        for m in self.mocks:
            m.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for m in self.mocks:
            m.__exit__(exc_type, exc_value, traceback)


class ClearCacheMixin:
    """
    TestCase mixin to clear the Django cache in setUp/tearDown
    """

    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        super().tearDown()
        cache.clear()
