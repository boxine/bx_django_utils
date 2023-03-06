import json
from functools import partial

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.fields import InvalidJSONInput
from django.utils.translation import get_language


class TranslationWidget(forms.Widget):
    template_name = 'bx_django_utils/translation_input.html'

    def __init__(self, language_codes, attrs=None):
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

    def __init__(self, language_codes, *args, **kwargs):
        kwargs['null'] = False
        kwargs['default'] = FieldTranslation
        self.language_codes = frozenset(language_codes)
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
        return FieldTranslation(**value)

    def clean(self, value, model_instance):
        value = super().clean(value, model_instance)
        existing_codes = value.keys()
        unknown_codes = existing_codes - self.language_codes
        if unknown_codes:
            raise ValidationError(f'Unknown translation language(s): {", ".join(sorted(unknown_codes))}')
        return value

    def to_python(self, value):
        if value is None:
            return FieldTranslation()
        if isinstance(value, FieldTranslation):
            return value
        if isinstance(value, dict):
            return FieldTranslation(**value)
        err = ValidationError('Invalid input for FieldTranslation instance.')
        if isinstance(value, str):
            try:
                return FieldTranslation(**json.loads(value, cls=self.decoder))
            except json.JSONDecodeError as ex:
                raise err from ex
        raise err

    def formfield(self, **kwargs):
        kwargs['form_class'] = TranslationFormField
        kwargs['widget_class'] = self.widget_class
        kwargs['language_codes'] = self.language_codes
        return super().formfield(**kwargs)


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
