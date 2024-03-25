import functools
from typing import TYPE_CHECKING

from django.core.cache.backends.base import memcache_key_warnings
from django.core.exceptions import ValidationError

from bx_django_utils.feature_flags.exceptions import FeatureFlagDisabled


if TYPE_CHECKING:
    from bx_django_utils.feature_flags.data_classes import FeatureFlag


def validate_cache_key(cache_key: str) -> None:
    messages = list(memcache_key_warnings(cache_key))
    if messages:
        raise ValidationError(messages)


def if_feature(feature_flag: "FeatureFlag", raise_exception: bool = False):
    """
    A decorator that only executed the decorated function if the given feature flag is enabled.
    Performs a noop otherwise, or raises a FeatureFlagDisabled exception if raise_exception is True.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not feature_flag.is_enabled:
                if not raise_exception:
                    return
                else:
                    raise FeatureFlagDisabled(feature_flag)
            return func(*args, **kwargs)

        return wrapper

    return decorator
