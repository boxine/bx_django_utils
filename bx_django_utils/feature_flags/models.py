from django.db import models
from django.utils.translation import gettext_lazy as _

from bx_django_utils.feature_flags.state import State
from bx_django_utils.models.timetracking import TimetrackingBaseModel


class FeatureFlagModel(TimetrackingBaseModel):
    """"""  # noqa - Don't add to README

    cache_key = models.CharField(
        primary_key=True,
        max_length=255,
        verbose_name=_('FeatureFlagModel.cache_key.verbose_name'),
        help_text=_('FeatureFlagModel.cache_key.help_text'),
    )
    state = models.SmallIntegerField(
        choices=State.choices,
        verbose_name=_('FeatureFlagModel.state.verbose_name'),
        help_text=_('FeatureFlagModel.state.help_text'),
    )

    def __str__(self):
        return f'{self.cache_key} {self.state}'

    class Meta:
        verbose_name = _('FeatureFlagModel.verbose_name')
        verbose_name_plural = _('FeatureFlagModel.verbose_name_plural')
