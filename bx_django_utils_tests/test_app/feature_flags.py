"""
    Example "Feature Flags"
"""
import inspect

from bx_django_utils.feature_flags.data_classes import FeatureFlag


foo_feature_flag = FeatureFlag(
    cache_key='foo',
    human_name='Foo',
    description=inspect.cleandoc(
        '''
        En-/disable example Feature flag `Foo`.
        Just for demonstrate.
        '''
    ),
    initial_enabled=True,
)

bar_feature_flag = FeatureFlag(
    cache_key='bar',
    human_name='Bar',
    description=inspect.cleandoc(
        '''
        En-/disable example Feature flag `Bar`.
        '''
    ),
    initial_enabled=False,
)
