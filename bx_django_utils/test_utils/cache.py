from unittest import mock

from django.core.cache import cache


class MockCache:
    """
    Mock Django cache backend, so it's easy to check/manipulate the cache content
    """

    def __init__(self):
        self.data = {}
        self.mocks = [
            mock.patch('django.core.cache.cache.get', self.get),
            mock.patch('django.core.cache.cache.set', self.set),
            mock.patch('django.core.cache.cache.delete', self.delete),
        ]

    def set(self, key, value, timeout=None):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        if key in self.data:
            del self.data[key]

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
