from django.core import validators
from django.db import models
from django.utils.translation import gettext_lazy as _


class HexColorValidator(validators.RegexValidator):
    """
    Hex color validator (seven-character hexadecimal notation, e.g.: "#0055ff")
    """
    regex = r'^#[0-9a-fA-F]{6}$'
    message = _('Enter a valid seven-character hexadecimal color value.')


class ColorModelField(models.CharField):
    """
    Hex color model field, e.g.: "#0055ff" (It's not a html color picker widget)

    Note: It's not a html color picker, because "<input type="color">" doesn't allow
    empty values! It will always fallback to "#000000"

    If you need a fancy color picker use e.g.: "django-colorfield" ;)
    """
    description = _('Color field (seven-character hexadecimal notation) e.g.: "#0055ff"')

    def __init__(self, **kwargs):
        kwargs['max_length'] = 7
        super().__init__(**kwargs)
        self.validators.append(validators.MinLengthValidator(self.max_length))
        self.validators.append(HexColorValidator())
