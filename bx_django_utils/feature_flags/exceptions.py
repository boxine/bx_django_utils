from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bx_django_utils.feature_flags.data_classes import FeatureFlag


class NotUniqueFlag(AssertionError):
    """"""  # noqa - don't add in README

    pass


class FeatureFlagDisabled(Exception):
    """"""  # noqa - don't add in README

    def __init__(self, feature_flag: "FeatureFlag", *args, **kwargs):
        msg = f'feature flag {feature_flag.human_name!r} is disabled'
        super().__init__(msg, *args, **kwargs)
