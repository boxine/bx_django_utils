from django.core.cache.backends.base import memcache_key_warnings
from django.core.exceptions import ValidationError


def validate_cache_key(cache_key: str) -> None:
    messages = list(memcache_key_warnings(cache_key))
    if messages:
        raise ValidationError(messages)
