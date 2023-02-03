from django.db import models
from django.utils.translation import gettext_lazy as _


class State(models.IntegerChoices):
    """"""  # noqa - don't add in README

    ENABLED = 1, _('enabled')
    DISABLED = 0, _('disabled')
