import dataclasses
from uuid import UUID

from django.core.cache import cache


@dataclasses.dataclass
class CachedDataclassBase:
    """
    A Base dataclass that can be easy store/restore to Django cache.
    """

    # Sady, it's not possible to mix non-default and default arguments with inheritance.
    # So the child class must define this:
    #
    # uuid: UUID = dataclasses.field(default_factory=uuid4)
    #

    def __post_init__(self):
        # Check if child class set a UUID:
        assert hasattr(self, 'uuid'), 'Child class must define a "uuid" value!'
        assert isinstance(self.uuid, UUID), f'A UUID is needed. Found: {type(self.uuid).__name__}'

    @property
    def cache_timeout(self):
        """
        Timeout used in cache.set() - To be overwritten, if needed.
        """
        return 1 * 60 * 60

    @classmethod
    def generate_cache_key(cls, uuid):
        prefix = cls.__name__
        cache_key = f'{prefix}-{uuid}'
        return cache_key

    def store2cache(self):
        """
        Save the current data to Django's cache.
        """
        cache_key = self.generate_cache_key(self.uuid)
        data_dict = dataclasses.asdict(self)
        cache.set(cache_key, data_dict, timeout=self.cache_timeout)

    @classmethod
    def get_from_cache(cls, uuid):
        """
        Restore data from Django's cache, if available.
        """
        cache_key = cls.generate_cache_key(uuid=uuid)
        if data_dict := cache.get(cache_key):
            return cls(**data_dict)

    def delete_cache_entry(self):
        """
        Remove data in Django's cache.
        """
        cache_key = self.generate_cache_key(self.uuid)
        return cache.delete(cache_key)
