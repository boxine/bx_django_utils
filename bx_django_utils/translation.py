import json
from functools import partial
from typing import Union

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.fields import InvalidJSONInput
from django.utils.text import slugify
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from bx_django_utils.models.manipulate import CreateOrUpdateResult, FieldUpdate, update_model_field


class TranslationWidget(forms.Widget):
    template_name = 'bx_django_utils/translation_input.html'

    def __init__(self, language_codes: tuple, attrs=None):
        self.language_codes = language_codes
        super().__init__(attrs=attrs)

    def format_value(self, value):
        # for some reason, value is always a string. convert back to dict.
        return json.loads(value)

    def value_from_datadict(self, data, files, name):
        fieldnames = {f'{name}__{code}': code for code in self.language_codes}  # e.g. "fieldname__de-de" -> "de-de"
        return {  # e.g. "de-de" -> "the translation string"
            fieldnames[fieldname]: data[fieldname] for fieldname in data if fieldname in fieldnames
        }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['language_codes'] = self.language_codes
        return context


class MultilineTranslationWidget(TranslationWidget):
    template_name = 'bx_django_utils/translation_input_multiline.html'


class TranslationFormField(forms.JSONField):
    """
    Default form field for TranslationField.
    """

    widget = None  # set by __init__

    def __init__(self, *args, language_codes, widget_class=TranslationWidget, **kwargs):
        self.widget = widget_class
        # self.widget can be a class or an instance.
        # abuse that to pass the language codes of the related TranslationField
        # to the widget.
        self.widget = self.widget(language_codes=language_codes)
        super().__init__(*args, **kwargs)

    def bound_data(self, data, initial):
        if self.disabled:
            return initial
        if data is None:
            return None
        if isinstance(data, str):
            try:
                return json.loads(data, cls=self.decoder)
            except json.JSONDecodeError:
                return InvalidJSONInput(data)
        return data


class FieldTranslation(dict):
    """
    Dict-like container that maps language codes to a translated string.
    Is returned when accessing the value of TranslationField.
    """

    UNTRANSLATED = '<UNTRANSLATED>'

    def get_first(self, codes):
        """
        Returns the first translation found for the given language codes.
        """
        for code in codes:
            if translation := self.get(code):
                return translation
        return self.UNTRANSLATED

    def __repr__(self):
        return f'FieldTranslation({super().__repr__()})'


class TranslationField(models.JSONField):
    """
    A field designed to hold translations for a given set of language codes.
    You may optionally define which widget this field should render as by default via
    the `widget_class` kwarg. The widget must always return a dict-like value, so
    it can be stored as JSON in the database.

    TranslationFields always have null=True. If no value is set, an empty dict will
    be used instead. This ensures a consistent way to access the data.

    Accessing this field's value returns a FieldTranslation instance instead of
    a regular dict (much like FileField returns a FieldFile instance).
    """

    default_error_messages = {
        # Replace "This field cannot be blank." a more appropriate message:
        'blank': _('At least one translation is required.'),
    }

    def __init__(self, language_codes: tuple, *args, **kwargs):
        kwargs['null'] = False
        kwargs['default'] = FieldTranslation
        self.language_codes = language_codes
        self.widget_class = kwargs.pop('widget_class', TranslationWidget)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        for override in ('null', 'default'):
            # TranslationField hardcodes values for these kwargs in __init__,
            # so omit them from deconstruction
            kwargs.pop(override, None)
        args = [self.language_codes, *args]
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        if value is None:
            return FieldTranslation()
        value = remove_empty_translations(value)  # Ignore empty translation from DB
        return FieldTranslation(value)

    def get_db_prep_save(self, value, *args, **kwargs):
        value = remove_empty_translations(value)  # Don't store empty translations to DB
        return super().get_db_prep_save(value, *args, **kwargs)

    def clean(self, value, model_instance):
        value = super().clean(value, model_instance)
        value = remove_empty_translations(value)
        existing_codes = value.keys()
        unknown_codes = existing_codes - self.language_codes
        if unknown_codes:
            raise ValidationError(f'Unknown translation language(s): {", ".join(sorted(unknown_codes))}')
        return value

    def to_python(self, value):
        if not value:
            return FieldTranslation()

        if isinstance(value, str):
            try:
                value = json.loads(value, cls=self.decoder)
            except json.JSONDecodeError as err:
                raise ValidationError(f'Invalid JSON data: {err}')
        if not isinstance(value, dict):
            raise ValidationError(f'Invalid input type: {type(value).__name__}')

        value = remove_empty_translations(value)
        return FieldTranslation(value)

    def formfield(self, **kwargs):
        kwargs['form_class'] = TranslationFormField
        kwargs['widget_class'] = self.widget_class
        kwargs['language_codes'] = self.language_codes
        return super().formfield(**kwargs)


def slug_generator(source_text):
    slug = slugify(source_text)
    yield slug
    max_loops = getattr(settings, 'MAX_UNIQUE_QUERY_ATTEMPTS', 1000)
    for number in range(2, max_loops + 1):
        yield f'{slug}-{number}'


def get_unique_translation_slug(*, model_instance, attr_name, source_text, lang_code):
    ModelClass = model_instance.__class__
    base_qs = ModelClass.objects.all()
    if pk := model_instance.pk:
        base_qs = base_qs.exclude(pk=pk)

    for slug_candidate in slug_generator(source_text):
        qs = base_qs.filter(**{f'{attr_name}__{lang_code}': slug_candidate})
        if not qs.exists():
            return slug_candidate

    raise RuntimeError(f'Can not find a unique slug for {model_instance} {attr_name=} {lang_code=}, {source_text=}')


class TranslationSlugField(TranslationField):
    """
    A unique translation slug field, useful in combination with TranslationField()
    e.g.:

        class TranslatedSlugTestModel(models.Model):
            LANGUAGE_CODES = ('de-de', 'en-us', 'es')

            translated = TranslationField(language_codes=LANGUAGE_CODES)
            translated_slug = TranslationSlugField(
                language_codes=LANGUAGE_CODES,
                populate_from='translated',
            )

    All slugs will be unique for every language, by adding a number, started with the second one.
    But Note:
          The field set `unique=True`, but the database level will only deny
          create non-unique slugs, if *all* translations are the same!
          So be careful if you use bulk create/update with not unique data!
          See Tests.
    """

    def __init__(self, *args, populate_from: str = None, **kwargs):
        self.populate_from = populate_from

        kwargs['blank'] = True
        kwargs['unique'] = True
        super().__init__(*args, **kwargs)
        assert self.blank is True, 'TranslationSlugField must always set blank=True !'

    def create_slug(self, model_instance, add):
        slug_translations = getattr(model_instance, self.attname)
        assert isinstance(
            slug_translations, (FieldTranslation, dict)
        ), f'Unexpected type: {type(slug_translations).__name__}'

        populate_translations = getattr(model_instance, self.populate_from)
        assert isinstance(
            populate_translations, (FieldTranslation, dict)
        ), f'Unexpected type: {type(populate_translations).__name__}'

        for lang_code in self.language_codes:
            source_text = slug_translations.get(lang_code) or populate_translations.get(lang_code)
            if source_text:
                slug = get_unique_translation_slug(
                    model_instance=model_instance,
                    attr_name=self.attname,
                    source_text=source_text,
                    lang_code=lang_code,
                )
                assert slug
                slug_translations[lang_code] = slug

        return slug_translations

    def pre_save(self, model_instance, add):
        value = self.create_slug(model_instance, add)
        return value


class TranslationFieldAdmin(admin.ModelAdmin):
    """
    Provides drop-in support for ModelAdmin classes that want to display TranslationFields
    in their changelist.

    Since TranslationFields are essentially a JSONField, the Django admin will _always_ render
    them as a serialized JSON objects (see django.contrib.admin.utils.display_for_field).
    This is not helpful in the context of TranslationField, so this base class does some
    patching to display one of the translations instead.
    """

    @staticmethod
    def get_translation_order(fallback_codes):
        """
        Determines the order in which a suitable translation is picked from the value of a TranslationField.
        Can be overriden by inheriting admin classes, e.g. when using language codes other
        than those the Django translation system uses.
        """
        return [
            get_language(),  # equal to current locale of user
            settings.LANGUAGE_CODE,
            *fallback_codes,
        ]

    def _get_translated_field_display(self, obj, fieldname, field_codes):
        field = getattr(obj, fieldname)
        order = self.get_translation_order(field_codes)
        trans = field.get_first(order)
        return trans

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # collect names of fields that are TranslationFields.
        # also save the translation codes for each field.
        # these will be used below for resolving a user-appropriate translation.
        translation_fields = []
        translation_codes = {}
        for field in self.model._meta.fields:
            if not isinstance(field, TranslationField):
                continue
            translation_fields.append(field.name)
            translation_codes[field.name] = field.language_codes

        # add a 'get_<fieldname>' method to the admin for each TranslationField found in the last step.
        # the method returns its most suitable translation.
        for field in translation_fields:
            resolve_func = partial(
                self._get_translated_field_display,
                fieldname=field,
                field_codes=translation_codes[field],
            )
            resolve_func.__name__ = field
            setattr(self, f'get_{field}', resolve_func)

        def patch_fieldnames(fieldnames):
            return [f'get_{field}' if field in translation_fields else field for field in fieldnames]

        # patch each list of fieldnames considered by the changelist to use the new 'get_<fieldname>' methods.
        self.list_display = patch_fieldnames(self.list_display)
        self.list_display_links = patch_fieldnames(self.list_display_links)
        self.readonly_fields = patch_fieldnames(self.readonly_fields)


def create_or_update_translation_callback(*, instance, field_name, old_value, new_value, result: CreateOrUpdateResult):
    """
    Callback for create_or_update2() for TranslationField, that will never remove existing translation.
    """
    if old_value == new_value:
        # Nothing to update -> we are done.
        return

    model_field = instance._meta.get_field(field_name)
    if not isinstance(model_field, TranslationField):
        # Normal model field -> use origin callback
        return update_model_field(
            instance=instance,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            result=result,
        )

    # Merge translations:
    merged_value = merge_translations(old_value, new_value)

    if old_value == merged_value:
        # Nothing to update -> we are done.
        return

    # The model field value has been changed -> set it on the model instance:
    setattr(instance, field_name, merged_value)

    # Expand the list of updated fields, used for result and save() call:
    result.updated_fields.append(field_name)

    # Store update information:
    result.update_info.append(FieldUpdate(field_name=field_name, old_value=old_value, new_value=merged_value))


def remove_empty_translations(translations: Union[dict, FieldTranslation]) -> FieldTranslation:
    """
    Remove all empty/None from a FieldTranslation, e.g.:

    >>> remove_empty_translations({'de-de': 'Hallo', 'en': 'Hello', 'es':'', 'mx': None})
    FieldTranslation({'de-de': 'Hallo', 'en': 'Hello'})
    """
    filtered = {lang_code: text for lang_code, text in translations.items() if text}
    return FieldTranslation(filtered)


def merge_translations(
    translations1: Union[dict, FieldTranslation], translations2: Union[dict, FieldTranslation]
) -> FieldTranslation:
    """
    Merge two FieldTranslation and ignore all empty/None values, e.g.:

    >>> merge_translations({'de': 'Hallo', 'en': '', 'es': 'Hola'}, {'de': '', 'es': 'HOLA'})
    FieldTranslation({'de': 'Hallo', 'es': 'HOLA'})
    """
    merged = remove_empty_translations(translations1)
    merged.update(remove_empty_translations(translations2))
    return FieldTranslation(merged)
