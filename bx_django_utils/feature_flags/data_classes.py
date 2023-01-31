import logging
from collections.abc import Iterable
from typing import Optional

from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _

from bx_django_utils.feature_flags.exceptions import NotUniqueFlag
from bx_django_utils.feature_flags.utils import validate_cache_key


logger = logging.getLogger(__name__)


class State(models.IntegerChoices):
    """"""  # noqa - don't add in README

    ENABLED = 1, _('enabled')
    DISABLED = 0, _('disabled')


class FeatureFlag:
    """
    A feature flag that persistent the state into django cache.
    """

    registry = {}

    def __init__(
        self,
        *,
        cache_key: str,
        human_name: str,
        initial_enabled: bool,
        description: Optional[str] = None,
        cache_key_prefix: str = 'feature-flags',
    ):
        self.human_name = human_name
        self.description = description

        validate_cache_key(cache_key)
        validate_cache_key(cache_key_prefix)
        self.cache_key = f'{cache_key_prefix}-{cache_key}'
        validate_cache_key(self.cache_key)  # Double check ;)

        if self.cache_key in self.registry:
            raise NotUniqueFlag(f'Cache key {self.cache_key !r} already registered!')

        self.registry[self.cache_key] = self

        if initial_enabled:
            self.initial_state = State.ENABLED
        else:
            self.initial_state = State.DISABLED

    def enable(self) -> None:
        self.set_state(new_state=State.ENABLED)

    def disable(self) -> None:
        self.set_state(new_state=State.DISABLED)

    def set_state(self, new_state: State) -> None:
        assert isinstance(
            new_state, State
        ), f'Given {new_state!r} (type: {type(new_state).__name__}) is not a State object!'

        cache.set(self.cache_key, new_state.value, timeout=None)  # set forever

    @property
    def is_enabled(self) -> bool:
        try:
            raw_value = cache.get(self.cache_key)
        except Exception as err:
            logger.exception('Get cache key %r failed: %s', self.cache_key, err)
            raw_value = None  # Use the initial state

        if raw_value is None:
            # Not set, yet
            return self.initial_state is State.ENABLED
        elif raw_value == State.ENABLED.value:
            return True
        return False

    @property
    def state(self):
        if self.is_enabled:
            return State.ENABLED
        else:
            return State.DISABLED

    @property
    def opposite_state(self):
        """
        returns the opposite of current "state".
        Usefull to toggle the state via set_state()
        """
        if self.is_enabled:
            return State.DISABLED
        else:
            return State.ENABLED

    @classmethod
    def values(cls) -> Iterable["FeatureFlag"]:
        yield from cls.registry.values()

    @classmethod
    def get_by_cache_key(cls, cache_key) -> "FeatureFlag":
        return cls.registry[cache_key]
