import dataclasses
from typing import Any
from uuid import UUID, uuid4

from django.core.cache import cache
from django.test import SimpleTestCase

from bx_django_utils.cached_dataclasses import CachedDataclassBase
from bx_django_utils.test_utils.cache import ClearCacheMixin


@dataclasses.dataclass
class ExampleCachedDataclass(CachedDataclassBase):
    integer: int
    dictionary: dict
    uuid: UUID = dataclasses.field(default_factory=uuid4)


@dataclasses.dataclass
class NoUUID(CachedDataclassBase):
    pass


@dataclasses.dataclass
class NoDefaultUUID(CachedDataclassBase):
    uuid: Any = None


class TestCachedDataclass(ClearCacheMixin, SimpleTestCase):
    def test_generate_cache_key(self):
        self.assertEqual(
            ExampleCachedDataclass.generate_cache_key(uuid=UUID(int=1)),
            'ExampleCachedDataclass-00000000-0000-0000-0000-000000000001',
        )

    def test_store_restore_to_cache(self):
        data = ExampleCachedDataclass(integer=1, dictionary={'foo': 'bar'})
        uuid_value = data.uuid
        cache_key = ExampleCachedDataclass.generate_cache_key(uuid=uuid_value)

        # Nothing cached, yet?
        self.assertIsNone(cache.get(cache_key))
        self.assertIsNone(ExampleCachedDataclass.get_from_cache(uuid=uuid_value))

        # Add data to Django's cache:
        data.store2cache()

        # Cached filled?
        cached_data = cache.get(cache_key)
        self.assertEqual(
            cached_data,
            {'dictionary': {'foo': 'bar'}, 'integer': 1, 'uuid': uuid_value},
        )

        # Get data back from cache:
        data2 = ExampleCachedDataclass.get_from_cache(uuid=uuid_value)
        self.assertIsInstance(data2, ExampleCachedDataclass)
        self.assertEqual(data, data2)

        # Delete cache entry:
        deleted = data.delete_cache_entry()
        self.assertTrue(deleted)
        self.assertIsNone(ExampleCachedDataclass.get_from_cache(uuid=uuid_value))

    def test_no_uuid_argument(self):
        with self.assertRaisesMessage(AssertionError, 'Child class must define a "uuid" value!'):
            NoUUID()

        with self.assertRaisesMessage(AssertionError, 'A UUID is needed. Found: NoneType'):
            NoDefaultUUID(uuid=None)

        uuid_value = UUID(int=0)
        data = NoDefaultUUID(uuid=uuid_value)
        self.assertIsInstance(data, NoDefaultUUID)
        self.assertEqual(data.uuid, UUID('00000000-0000-0000-0000-000000000000'))
