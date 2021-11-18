import threading

from bx_py_utils.dict_utils import pluck
from django.db import models

from bx_django_utils.data_types.gtin.model_fields import GtinModelField
from bx_django_utils.models.color_field import ColorModelField
from bx_django_utils.models.timetracking import TimetrackingBaseModel


class TimetrackingTestModel(TimetrackingBaseModel):
    pass


class CreateOrUpdateTestModel(TimetrackingBaseModel):
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)

    many2one_rel = models.ForeignKey(
        TimetrackingTestModel,
        on_delete=models.CASCADE,
        blank=True, null=True
    )

    blank_field = models.CharField(max_length=64, blank=True)
    null_field = models.CharField(max_length=64, blank=True, null=True)


class GtinFieldTestModel(models.Model):
    default_gtin = GtinModelField()  # accept default length: 12,13 and 14
    all_gtin = GtinModelField(
        blank=True,
        accepted_length=(8, 10, 12, 13, 14)
    )
    ean13 = GtinModelField(
        blank=True, null=True,
        accepted_length=(13,)  # accept one length
    )


class ColorFieldTestModel(models.Model):
    required_color = ColorModelField()
    optional_color = ColorModelField(blank=True, null=True)



class StoreSaveModel(models.Model):
    name = models.CharField(max_length=64)
    _save_calls = threading.local()

    def save(self, **kwargs):
        if not hasattr(self._save_calls, 'saves'):
            self._save_calls.saves = []

        self._save_calls.saves.append(pluck(kwargs, ('arg', 'other_arg')))
        if 'arg' in kwargs:
            del kwargs['arg']
        if 'other_arg' in kwargs:
            del kwargs['other_arg']

        return super().save(**kwargs)
