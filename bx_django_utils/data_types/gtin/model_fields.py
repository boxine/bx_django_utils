from django.db.models import CharField
from django.utils.translation import gettext_lazy as _
from stdnum import ean

from bx_django_utils.data_types.gtin.constants import DEFAULT_ACCEPT_LENGTH
from bx_django_utils.data_types.gtin.form_fields import GtinFormField
from bx_django_utils.data_types.gtin.validators import GtinValidator


class GtinModelField(CharField):
    """
    GTIN model field
    """
    description = _('GTIN number')

    def __init__(self, *args, accepted_length=DEFAULT_ACCEPT_LENGTH, **kwargs):
        self.accepted_length = accepted_length
        kwargs['max_length'] = max(accepted_length)
        kwargs['verbose_name'] = kwargs.get('verbose_name') or 'GTIN'
        kwargs['validators'] = [GtinValidator(accepted_length=accepted_length)]
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value:
            value = ean.compact(value)
        return super().to_python(value)

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': GtinFormField,
            'validators': [GtinValidator(accepted_length=self.accepted_length)],
            **kwargs,
        })
