from django import forms
from django.db import models

from bx_django_utils.credentials.utils import decrypt, encrypt


class EncryptedCharField(models.CharField):
    """
    A CharField that automatically stores its data in an encrypted state.
    """

    def get_internal_type(self):
        return 'BinaryField'

    def get_db_prep_save(self, value, connection):
        value = super().get_db_prep_save(value, connection)
        if value is not None:
            encrypted = encrypt(value)
            return connection.Database.Binary(encrypted)

    def from_db_value(self, value, expression, connection, *args):
        if value is not None:
            # Django returns memoryview objects instead of bytes for BinaryFields
            # when the connected db is Postgres, see https://code.djangoproject.com/ticket/27813
            if isinstance(value, memoryview):
                value = bytes(value)
            return self.to_python(decrypt(value))

    def formfield(self, **kwargs):
        kwargs['widget'] = forms.PasswordInput
        return super().formfield(**kwargs)
