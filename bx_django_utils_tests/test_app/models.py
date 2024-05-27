import threading

from bx_py_utils.dict_utils import pluck
from django.db import models
from polymorphic.models import PolymorphicModel

from bx_django_utils.data_types.gtin.model_fields import GtinModelField
from bx_django_utils.models.color_field import ColorModelField
from bx_django_utils.models.timetracking import TimetrackingBaseModel
from bx_django_utils.translation import MultilineTranslationWidget, TranslationField, TranslationSlugField


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
    uuid_field = models.UUIDField(blank=True, null=True)


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


class TranslatedModel(models.Model):
    LANGUAGE_CODES = ('de-de', 'en-us', 'es')  # Old, deprecated
    LANGUAGES = (
        ('de-de', 'German'),
        ('en-us', 'US-English'),
        ('es', 'Spanish'),
    )

    translated = TranslationField(
        language_codes=LANGUAGE_CODES,  # Old, deprecated argument
        blank=False,
    )
    translated_multiline = TranslationField(
        languages=LANGUAGES,
        blank=True,
        widget_class=MultilineTranslationWidget,
    )
    not_translated = models.TextField(default='A Default Value')


class RawTranslatedModel(models.Model):
    translated = models.JSONField()
    translated_multiline = models.JSONField(blank=True, default=dict)
    not_translated = models.TextField(default='A Default Value')

    class Meta:
        managed = False
        db_table = TranslatedModel._meta.db_table


class TranslatedSlugTestModel(models.Model):
    LANGUAGE_CODES = ('de-de', 'en-us', 'es')  # Old, deprecated
    LANGUAGES = (
        ('de-de', 'German'),
        ('en-us', 'US-English'),
        ('es', 'Spanish'),
    )

    translated = TranslationField(languages=LANGUAGES)
    translated_slug = TranslationSlugField(
        language_codes=LANGUAGE_CODES,  # Old, deprecated argument
        populate_from='translated',
    )


class NonUniqueTranslatedSlugTestModel(models.Model):
    LANGUAGES = (
        ('de-de', 'German'),
        ('en-us', 'US-English'),
        ('es', 'Spanish'),
    )

    translated = TranslationField(languages=LANGUAGES)
    translated_slug = TranslationSlugField(
        languages=LANGUAGES,
        populate_from='translated',
        unique=False,
    )


class ConnectedUniqueSlugModel1(models.Model):
    LANGUAGES = (
        ('de-de', 'German'),
        ('en-us', 'US-English'),
        ('es', 'Spanish'),
    )

    translated = TranslationField(languages=LANGUAGES)
    translated_slug = TranslationSlugField(
        languages=LANGUAGES,
        populate_from='translated',
        additional_uniqueness=(
            dict(
                app_label='test_app',
                model_name='ConnectedUniqueSlugModel2',
                field_name='translated_slug',
            ),
        ),
    )


class ConnectedUniqueSlugModel2(models.Model):
    LANGUAGES = (
        ('de-de', 'German'),
        ('en-us', 'US-English'),
        ('es', 'Spanish'),
    )

    translated = TranslationField(languages=LANGUAGES)
    translated_slug = TranslationSlugField(
        languages=LANGUAGES,
        populate_from='translated',
        additional_uniqueness=(
            dict(
                app_label='test_app',
                model_name='ConnectedUniqueSlugModel1',
                field_name='translated_slug',
            ),
        ),
    )


class ValidateLengthTranslations(models.Model):
    LANGUAGES = (
        ('de', 'German'),
        ('en', 'English'),
    )

    translated = TranslationField(min_value_length=3, max_value_length=20, languages=LANGUAGES)
    translated_slug = TranslationSlugField(
        min_value_length=3, max_value_length=20, languages=LANGUAGES, populate_from='translated'
    )


class PolymorphicVehicle(PolymorphicModel):
    license_plate = models.CharField(max_length=64, primary_key=True)
    color = models.TextField()


class PolymorphicCar(PolymorphicVehicle):
    pass


class PolymorphicBike(PolymorphicVehicle):
    pass
