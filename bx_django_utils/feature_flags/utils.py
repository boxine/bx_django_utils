import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from bx_django_utils.feature_flags.exceptions import FeatureFlagDisabled

if TYPE_CHECKING:
    from bx_django_utils.feature_flags.data_classes import FeatureFlag


def if_feature(
    feature_flag: "FeatureFlag",
    raise_exception: bool = False,
    retval_factory: Callable[[], Any] | None = None,
):
    """
    A decorator that only executes the decorated function if the given feature flag is enabled.

    :param feature_flag: The feature flag to consider.
    :param retval_factory: A factory that returns the value to be returned when the feature flag is disabled.
    :param raise_exception: If True, raises a FeatureFlagDisabled exception if the feature flag is disabled.
    """
    if raise_exception and retval_factory is not None:
        raise ValueError('raise_exception=True and retval_factory are mutually exclusive')

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not feature_flag.is_enabled:
                if raise_exception:
                    raise FeatureFlagDisabled(feature_flag)
                if retval_factory is not None:
                    return retval_factory()
                return
            return func(*args, **kwargs)

        return wrapper

    return decorator
