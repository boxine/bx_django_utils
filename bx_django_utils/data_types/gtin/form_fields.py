from django import forms
from stdnum.ean import compact

from bx_django_utils.data_types.gtin.constants import DEFAULT_ACCEPT_LENGTH
from bx_django_utils.data_types.gtin.validators import GtinValidator


class GtinFormField(forms.CharField):
    """
    Form field with GTIN validator.
    """

    def __init__(self, *args, accepted_length=DEFAULT_ACCEPT_LENGTH, **kwargs):
        kwargs['min_length'] = min(accepted_length)
        kwargs['max_length'] = min(accepted_length) + 3  # +spaces, e.g.: '6 92771 98116 1'
        kwargs['validators'] = [GtinValidator(accepted_length=accepted_length)]
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if value:
            value = compact(value)  # Convert to the minimal representation
        return value

    def prepare_value(self, value):
        if value:
            value = compact(value)  # Convert to the minimal representation
        return value
