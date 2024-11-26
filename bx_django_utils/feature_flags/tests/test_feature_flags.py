import datetime

from django.test import TestCase

from bx_django_utils.feature_flags.data_classes import FeatureFlag
from bx_django_utils.feature_flags.exceptions import FeatureFlagDisabled, NotUniqueFlag
from bx_django_utils.feature_flags.models import FeatureFlagModel
from bx_django_utils.feature_flags.state import State
from bx_django_utils.feature_flags.test_utils import FeatureFlagTestCaseMixin
from bx_django_utils.feature_flags.utils import if_feature


class FeatureFlagsTestCase(FeatureFlagTestCaseMixin, TestCase):
    """"""  # noqa - Don't add to README

    warum_up_feature_flag_cache = False

    def setUp(self):
        super().setUp()

        FeatureFlag.registry.clear()
        self.initial_enabled_test_flag = FeatureFlag(
            cache_key='test-initial_enabled',
            human_name='A test flag that is initial "enabled"',
            initial_enabled=True,
        )
        self.initial_disabled_test_flag = FeatureFlag(
            cache_key='test-initial_disabled',
            human_name='A test flag that is initial "disabled"',
            initial_enabled=False,
        )

    def test_uniqueness(self):
        FeatureFlag(
            cache_key='test',
            human_name='Test Uniqueness 1',
            initial_enabled=True,
        )
        with self.assertRaisesMessage(
            NotUniqueFlag, "Cache key 'feature-flags-test' already registered!"
        ):
            FeatureFlag(
                cache_key='test',
                human_name='Test Uniqueness 2',
                initial_enabled=True,
            )

    def test_basic(self):
        test_keys = {'feature-flags-test-initial_enabled', 'feature-flags-test-initial_disabled'}
        self.assertEqual(FeatureFlag.registry.keys(), test_keys)

        seen_keys = set()
        for instance in FeatureFlag.values():
            self.assertIsInstance(instance, FeatureFlag)
            seen_keys.add(instance.cache_key)
        self.assertEqual(seen_keys, test_keys)

        # Initial state is enabled?
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.assertEqual(self.initial_enabled_test_flag.opposite_state, State.DISABLED)
        self.assertTrue(self.initial_enabled_test_flag.is_enabled)
        self.assertFalse(self.initial_enabled_test_flag.is_disabled)
        self.assertTrue(self.initial_enabled_test_flag)  # checks __bool__
        # Disable
        self.initial_enabled_test_flag.set_state(State.DISABLED)
        # is disabled?
        self.assertFalse(self.initial_enabled_test_flag.is_enabled)
        self.assertTrue(self.initial_enabled_test_flag.is_disabled)
        self.assertFalse(self.initial_enabled_test_flag)  # checks __bool__
        self.assertEqual(self.initial_enabled_test_flag.state, State.DISABLED)
        self.assertEqual(self.initial_enabled_test_flag.opposite_state, State.ENABLED)
        # enable via set_state:
        self.initial_enabled_test_flag.set_state(State.ENABLED)
        # is enabled?
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.assertEqual(self.initial_enabled_test_flag.opposite_state, State.DISABLED)
        self.assertTrue(self.initial_enabled_test_flag.is_enabled)

        # Just check the other initial state:
        self.assertEqual(self.initial_disabled_test_flag.state, State.DISABLED)
        self.assertEqual(self.initial_disabled_test_flag.opposite_state, State.ENABLED)
        self.assertFalse(self.initial_disabled_test_flag.is_enabled)

    def test_initial_state(self):
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.assertTrue(self.initial_enabled_test_flag.is_enabled)

        self.assertEqual(self.initial_disabled_test_flag.state, State.DISABLED)
        self.assertFalse(self.initial_disabled_test_flag.is_enabled)

    def test_set_state(self):
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.initial_enabled_test_flag.set_state(State.DISABLED)
        self.assertEqual(self.initial_enabled_test_flag.state, State.DISABLED)
        self.initial_enabled_test_flag.set_state(State.ENABLED)
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)

    def test_enable_disable(self):
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)
        self.initial_enabled_test_flag.disable()
        self.assertEqual(self.initial_enabled_test_flag.state, State.DISABLED)
        self.initial_enabled_test_flag.enable()
        self.assertEqual(self.initial_enabled_test_flag.state, State.ENABLED)

    def test_decorator(self):
        some_var = 0

        @if_feature(self.initial_enabled_test_flag)
        def increment():
            nonlocal some_var
            some_var += 1

        self.assertTrue(self.initial_enabled_test_flag)
        self.assertEqual(some_var, 0)
        increment()
        self.assertEqual(some_var, 1)

        self.initial_enabled_test_flag.disable()
        increment()
        self.assertEqual(some_var, 1)

    def test_decorator_with_retval_factory(self):
        def default_numbers() -> list[int]:
            return [97, 98, 99]

        @if_feature(self.initial_enabled_test_flag, retval_factory=default_numbers)
        def compute_numbers() -> list[int]:
            return [1, 2, 3]

        self.assertTrue(self.initial_enabled_test_flag)
        self.assertEqual(compute_numbers(), [1, 2, 3])
        self.initial_enabled_test_flag.disable()
        self.assertFalse(self.initial_enabled_test_flag)
        self.assertEqual(compute_numbers(), [97, 98, 99])

    def test_decorator_with_args(self):
        some_var = 0
        call_kwargs = None

        @if_feature(self.initial_enabled_test_flag)
        def increment(by, **kwargs):
            nonlocal some_var
            nonlocal call_kwargs
            some_var += by
            call_kwargs = kwargs

        self.assertTrue(self.initial_enabled_test_flag)
        self.assertEqual(some_var, 0)
        self.assertIsNone(call_kwargs)
        increment(2, foo=True)
        self.assertEqual(some_var, 2)
        self.assertEqual(call_kwargs, {'foo': True})

        self.initial_enabled_test_flag.disable()
        increment(3, foo=False)
        self.assertEqual(some_var, 2)
        self.assertEqual(call_kwargs, {'foo': True})

    def test_decorator_raising(self):
        some_var = 0

        @if_feature(self.initial_enabled_test_flag, raise_exception=True)
        def increment():
            nonlocal some_var
            some_var += 1

        self.assertTrue(self.initial_enabled_test_flag)
        self.assertEqual(some_var, 0)
        increment()
        self.assertEqual(some_var, 1)

        self.initial_enabled_test_flag.disable()
        with self.assertRaisesMessage(FeatureFlagDisabled, ''):
            increment()
        self.assertEqual(some_var, 1)

    def test_cache(self):
        duration = datetime.timedelta(seconds=60)
        ff = FeatureFlag(
            cache_key='cache-test',
            human_name='Cache Test',
            initial_enabled=True,
            cache_duration=duration,
        )
        self.assertTrue(ff)

        ff.disable()
        self.assertTrue(ff)  # still enabled due to caching!

        orig_time_func = ff._cache_time_func

        def future():
            return orig_time_func() + duration.total_seconds() + 1

        ff._cache_time_func = future
        self.assertFalse(ff)  # now it's disabled due to cache expiration


class IsolatedFeatureFlagsTestCase(FeatureFlagTestCaseMixin, TestCase):
    """"""  # noqa - Don't add to README

    def test_reset(self):
        flag = FeatureFlag(
            cache_key='reset-me',
            human_name='Testing reset',
            initial_enabled=False,
        )
        flag.enable()
        self.assertTrue(FeatureFlagModel.objects.filter(cache_key=flag.cache_key).exists())

        flag.reset()
        self.assertFalse(FeatureFlagModel.objects.filter(cache_key=flag.cache_key).exists())

        # Reset again – should not error
        flag.reset()

    def test_str(self):
        flag = FeatureFlag(
            cache_key='be-wild',
            human_name='Be wild',
            initial_enabled=False,
        )
        self.assertEqual(str(flag), '<FeatureFlag be-wild>')
        self.assertEqual(repr(flag), "FeatureFlag(cache_key='be-wild', human_name='Be wild', initial_enabled=False)")
