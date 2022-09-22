import os
import uuid

from bx_py_utils.anonymize import anonymize
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _

from bx_django_utils.credentials.fields import EncryptedCharField
from bx_django_utils.models.timetracking import TimetrackingBaseModel


class Credential(TimetrackingBaseModel):
    """
    Credential stores arbitrary key-value-pairs. The value is always stored encrypted.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('Credential.id.verbose_name'),
        help_text=_('Credential.id.help_text'),
    )
    key = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('Credential.key.verbose_name'),
        help_text=_('Credential.key.help_text'),
    )
    secret = EncryptedCharField(
        max_length=255,
        verbose_name=_('Credential.secret.verbose_name'),
        help_text=_('Credential.secret.help_text'),
    )

    def __str__(self):
        return self.key

    @admin.display(description=_('Credential.secret.verbose_name'))
    def secret_anonymized(self):
        return anonymize(self.secret)

    @classmethod
    def get(cls, key):
        """
        Tries to retrieve the secret for the given key.
        Checks multiple sources, in this order:
          1. database
          2. Django settings module
          3. environment variables
        The first value found will be returned.

        Raises a ValueError if the secret couldn't be resolved in any way.
        """
        try:
            return cls.objects.get(key=key).secret
        except cls.DoesNotExist:
            pass

        from_settings = getattr(settings, key, None)
        if from_settings is not None:
            return from_settings

        from_env = os.environ.get(key)
        if from_env is not None:
            return from_env

        raise ValueError(f'credential key {key} could not be found in db, env or settings')

    @classmethod
    def get_many(cls, *keys, check=True) -> tuple[str]:
        """
        Like get(), but for an arbitrary amount of keys.
        :check: Assert that all keys has values
        """
        values = []
        errors = []
        for key in keys:
            value = cls.get(key)
            values.append(value)
            if check and not value:
                errors.append(f'{key} not set')
        if errors:
            raise AssertionError(', '.join(errors))

        return tuple(values)
