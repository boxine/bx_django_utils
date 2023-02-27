import logging
from collections.abc import Iterable
from typing import Optional

from django.core.cache import cache

from bx_django_utils.feature_flags.exceptions import NotUniqueFlag
from bx_django_utils.feature_flags.models import FeatureFlagModel
from bx_django_utils.feature_flags.state import State
from bx_django_utils.feature_flags.utils import validate_cache_key
from bx_django_utils.models.manipulate import create_or_update2


logger = logging.getLogger(__name__)


class FeatureFlag:
    """
    A feature flag that persistent the state into django cache/database.
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

    def enable(self) -> bool:
        return self.set_state(new_state=State.ENABLED)

    def disable(self) -> bool:
        return self.set_state(new_state=State.DISABLED)

    def set_state(self, new_state: State) -> bool:
        """store state to database + cache and return it"""
        assert isinstance(
            new_state, State
        ), f'Given {new_state!r} (type: {type(new_state).__name__}) is not a State object!'

        state = self._add2cache(state_value=new_state.value)
        create_or_update2(
            ModelClass=FeatureFlagModel,
            lookup={'cache_key': self.cache_key},
            state=new_state,
        )
        return state

    def _add2cache(self, state_value: int) -> bool:
        """store state to cache and return it"""
        assert state_value in (0, 1), f'Unknown cache value: {state_value!r}'
        cache.set(self.cache_key, state_value, timeout=None)  # set forever
        return bool(state_value)

    @property
    def is_enabled(self) -> bool:
        try:
            raw_value = cache.get(self.cache_key)
        except Exception as err:
            # Will only happen, if cache backend is down
            logger.exception('Get cache key %r failed: %s', self.cache_key, err)
            raw_value = None  # Use the initial state

        if raw_value is None:
            # Not set, yet or cache was cleared -> Try to get the state from database
            instance = (
                FeatureFlagModel.objects.filter(cache_key=self.cache_key).values('state').first()
            )
            if instance:
                # We found the flag in database -> store state in the cache
                # and return the current state
                state_value = instance['state']
                return self._add2cache(state_value=state_value)
            else:
                # It's not in the cache and database -> store initial state in cache and database
                # and return the current state
                return self.set_state(new_state=self.initial_state)
        else:
            assert raw_value in (0, 1), f'Unknown cache value: {raw_value!r}'
            return bool(raw_value)

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
