import datetime
import logging
import time
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager

from bx_django_utils.feature_flags.exceptions import NotUniqueFlag
from bx_django_utils.feature_flags.models import FeatureFlagModel
from bx_django_utils.feature_flags.state import State
from bx_django_utils.models.manipulate import create_or_update2

logger = logging.getLogger(__name__)

DEFAULT_DURATION = datetime.timedelta(seconds=0)


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
        description: str | None = None,
        cache_key_prefix: str = 'feature-flags',
        cache_duration: datetime.timedelta = DEFAULT_DURATION,
    ):
        """
        :param cache_duration: how long the state of the flag should be cached in-process
        """
        self.human_name = human_name
        self.description = description

        self.name = cache_key
        self.cache_key = f'{cache_key_prefix}-{cache_key}'

        if self.cache_key in self.registry:
            raise NotUniqueFlag(f'Cache key {self.cache_key !r} already registered!')

        self.registry[self.cache_key] = self

        if initial_enabled:
            self.initial_state = State.ENABLED
        else:
            self.initial_state = State.DISABLED

        if cache_duration:
            self._cache_duration: datetime.timedelta = cache_duration
            self._cache_time_func: Callable[[], float] = time.monotonic
            self._cache_from: float = self._cache_time_func()
            self._cache_value: State = self.initial_state

    def enable(self) -> bool:
        return self.set_state(new_state=State.ENABLED)

    def disable(self) -> bool:
        return self.set_state(new_state=State.DISABLED)

    def set_state(self, new_state: State) -> bool:
        assert isinstance(
            new_state, State
        ), f'Given {new_state!r} (type: {type(new_state).__name__}) is not a State object!'

        obj = create_or_update2(
            ModelClass=FeatureFlagModel,
            lookup={'cache_key': self.cache_key},
            state=new_state,
        )

        return bool(obj.instance.state)

    def reset(self) -> None:
        FeatureFlagModel.objects.filter(cache_key=self.cache_key).delete()

    @property
    def is_enabled(self) -> bool:
        if not hasattr(self, '_cache_duration'):  # caching is disabled
            return self._compute_is_enabled()

        elapsed = self._cache_time_func() - self._cache_from

        # cache is still valid
        if elapsed <= self._cache_duration.total_seconds():
            return bool(self._cache_value.value)

        # cache is invalid -> recompute
        state = self._compute_is_enabled()
        self._cache_from = self._cache_time_func()
        self._cache_value = State(state)
        return state

    def _compute_is_enabled(self) -> bool:
        obj, _ = FeatureFlagModel.objects.get_or_create(
            cache_key=self.cache_key,
            defaults={'state': self.initial_state},
        )
        return bool(obj.state)

    @property
    def is_disabled(self) -> bool:
        return not self.is_enabled

    @contextmanager
    def temp_enable(self) -> Iterator[None]:
        """
        Temporarily enable the feature flag.
        """
        was_enabled = self.is_enabled
        if not was_enabled:
            self.enable()

        yield

        if not was_enabled:
            self.disable()

    @contextmanager
    def temp_disable(self) -> Iterator[None]:
        """
        Temporarily disable the feature flag.
        """
        was_disabled = self.is_disabled
        if not was_disabled:
            self.disable()

        yield

        if not was_disabled:
            self.enable()

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

    def __bool__(self):
        return self.is_enabled

    def __str__(self):
        return f'<FeatureFlag {self.name}>'

    def __repr__(self):
        initial = self.initial_state == State.ENABLED
        return f'FeatureFlag(cache_key={self.name!r}, human_name={self.human_name!r}, initial_enabled={initial!r})'
