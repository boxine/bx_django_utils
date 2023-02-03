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

    def enable(self) -> None:
        self.set_state(new_state=State.ENABLED)

    def disable(self) -> None:
        self.set_state(new_state=State.DISABLED)

    def set_state(self, new_state: State) -> None:
        assert isinstance(
            new_state, State
        ), f'Given {new_state!r} (type: {type(new_state).__name__}) is not a State object!'

        create_or_update2(
            ModelClass=FeatureFlagModel,
            lookup={'cache_key': self.cache_key},
            state=new_state,
        )
        self._add2cache(state_value=new_state.value)

    def _add2cache(self, state_value: int):
        assert state_value in (0, 1)
        cache.set(self.cache_key, state_value, timeout=None)  # set forever

    @property
    def is_enabled(self) -> bool:
        try:
            raw_value = cache.get(self.cache_key)
        except Exception as err:
            logger.exception('Get cache key %r failed: %s', self.cache_key, err)
            raw_value = None  # Use the initial state

        if raw_value is None:
            # Not set, yet or cache was cleared -> Try to get the state from database
            instance = (
                FeatureFlagModel.objects.filter(cache_key=self.cache_key).values('state').first()
            )
            if instance:
                # We found the flag in database -> store it in the cache
                state_value = instance['state']
                self._add2cache(state_value=state_value)
                return bool(state_value)

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
