from __future__ import annotations

import json
import warnings
from functools import partial
from itertools import chain

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.fields.json import KeyTransform
from django.forms.fields import InvalidJSONInput
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from bx_django_utils.admin_utils.admin_urls import admin_change_url
from bx_django_utils.models.manipulate import CreateOrUpdateResult, FieldUpdate, update_model_field


META_KEY = '_meta'


class TranslationWidget(forms.Widget):
    template_name = 'bx_django_utils/translation_input.html'

    def __init__(self, languages: tuple, attrs=None):
        self.languages = languages
        super().__init__(attrs=attrs)

    def format_value(self, value):
        # for some reason, value is always a string. convert back to dict.
        return json.loads(value)

    def value_from_datadict(self, data, files, name):
        fieldnames = {  # e.g. "fieldname__de-de" -> "de-de"
            f'{name}__{entry[0]}': entry[0] for entry in self.languages
        }
        res = {  # e.g. "de-de" -> "the translation string"
            fieldnames[fieldname]: data[fieldname] for fieldname in data if fieldname in fieldnames
        }
        if f'{name}__{META_KEY}' in data:
            meta_json = data[f'{name}__{META_KEY}']
            meta = json.loads(meta_json) if meta_json else {}
            res[META_KEY] = meta
        return res

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['languages'] = self.languages
        return context


class MultilineTranslationWidget(TranslationWidget):
    template_name = 'bx_django_utils/translation_input_multiline.html'


class TranslationFormField(forms.JSONField):
    """
    Default form field for TranslationField.
    """

    widget = None  # set by __init__

    def __init__(
        self,
        *args,
        languages: tuple,
        min_value_length: int | None = None,
        max_value_length: int | None = None,
        widget_class=TranslationWidget,
        **kwargs,
    ):
        self.min_value_length = min_value_length
        self.max_value_length = max_value_length

        self.widget = widget_class
        # self.widget can be a class or an instance.
        # abuse that to pass the language codes of the related TranslationField
        # to the widget.
        self.widget = self.widget(languages=languages)
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

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if self.max_value_length is not None and not widget.is_hidden:
            attrs["maxlength"] = str(self.max_value_length)
        if self.min_value_length is not None and not widget.is_hidden:
            attrs["minlength"] = str(self.min_value_length)
        return attrs


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

    The optional `min_value_length` and `max_value_length` options will apply to the individual translated text.
    """

    default_error_messages = {
        # Replace "This field cannot be blank." a more appropriate message:
        'blank': _('At least one translation is required.'),
    }

    def __init__(
        self,
        *args,
        language_codes: tuple | None = None,
        languages: tuple = None,
        min_value_length: int | None = None,
        max_value_length: int | None = None,
        **kwargs,
    ):
        kwargs['null'] = False
        kwargs['default'] = FieldTranslation

        if language_codes:
            warnings.warn(
                'language_codes argument is deprecated in favour of languages', DeprecationWarning, stacklevel=2
            )
            assert not languages, 'Remove language_codes argument!'
            self.languages = tuple((code, code) for code in language_codes)
        else:
            self.languages = languages

        self.min_value_length = min_value_length
        self.max_value_length = max_value_length
        self.widget_class = kwargs.pop('widget_class', TranslationWidget)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        for override in ('null', 'default'):
            # TranslationField hardcodes values for these kwargs in __init__,
            # so omit them from deconstruction
            kwargs.pop(override, None)

        kwargs['languages'] = self.languages
        kwargs['min_value_length'] = self.min_value_length
        kwargs['max_value_length'] = self.max_value_length
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)

        if isinstance(expression, KeyTransform) and (isinstance(value, str) or (value is None)):
            return value  # Getting just one translation, already done

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
        known_codes = {entry[0] for entry in self.languages}
        unknown_codes = existing_codes - known_codes - {META_KEY}
        if unknown_codes:
            raise ValidationError(f'Unknown translation language(s): {", ".join(sorted(unknown_codes))}')

        if self.min_value_length is not None or self.max_value_length is not None:
            errors = []
            for language_code, text in value.items():
                length = len(text)
                if self.max_value_length is not None and length > self.max_value_length:
                    errors.append(
                        ValidationError(
                            f'Ensure "{language_code}" translation has at most {self.max_value_length} character'
                            f' (it has {length}).'
                        )
                    )
                if self.min_value_length is not None and length < self.min_value_length:
                    errors.append(
                        ValidationError(
                            f'Ensure "{language_code}" translation has at least {self.min_value_length} character'
                            f' (it has {length}).'
                        )
                    )

            if errors:
                raise ValidationError(errors)

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
        kwargs['languages'] = self.languages

        kwargs['min_value_length'] = self.min_value_length
        kwargs['max_value_length'] = self.max_value_length

        return super().formfield(**kwargs)


def slug_generator(source_text):
    max_loops = getattr(settings, 'MAX_UNIQUE_QUERY_ATTEMPTS', 1000)

    slug = slugify(source_text)
    if not slug:
        # The source text doesn't contain any normal character
        # Fallback and yield numbers
        for number in range(1, max_loops + 1):
            yield str(number)
    else:
        yield slug
        for number in range(2, max_loops + 1):
            yield f'{slug}-{number}'


def additional_uniqueness_exists(*, additional_uniqueness: tuple[dict], lang_code, slug_candidate):
    for info in additional_uniqueness:
        ModelClass = apps.get_model(app_label=info['app_label'], model_name=info['model_name'])
        qs = ModelClass.objects.filter(**{f'{info["field_name"]}__{lang_code}': slug_candidate})
        if qs.exists():
            return True
    return False


def get_unique_translation_slug(
    *,
    model_instance,
    attr_name,
    source_text,
    lang_code,
    additional_uniqueness: tuple[dict] | None = None,
):
    ModelClass = model_instance.__class__
    base_qs = ModelClass.objects.all()
    if pk := model_instance.pk:
        base_qs = base_qs.exclude(pk=pk)

    for slug_candidate in slug_generator(source_text):
        qs = base_qs.filter(**{f'{attr_name}__{lang_code}': slug_candidate})
        if qs.exists():
            # Slug already exists in the same model -> try next candidate
            continue

        if additional_uniqueness and additional_uniqueness_exists(
            additional_uniqueness=additional_uniqueness, lang_code=lang_code, slug_candidate=slug_candidate
        ):
            # Slug already exists one of the other models -> try next candidate
            continue

        return slug_candidate

    raise RuntimeError(f'Can not find a unique slug for {model_instance} {attr_name=} {lang_code=}, {source_text=}')


class TranslationSlugField(TranslationField):
    """
    A unique translation slug field, useful in combination with TranslationField()
    All slugs will be unique for every language, by adding a number, started with the second one.

    e.g.:

        class TranslatedSlugTestModel(models.Model):
            LANGUAGE_CODES = ('de-de', 'en-us', 'es')

            translated = TranslationField(language_codes=LANGUAGE_CODES)
            translated_slug = TranslationSlugField(
                language_codes=LANGUAGE_CODES,
                populate_from='translated',
            )

    Optional: Uniqueness between more than one Model
    e.g.:

        class TranslatedSlugTestModel(models.Model):
            #...
            translated_slug = TranslationSlugField(
                language_codes=LANGUAGE_CODES,
                populate_from='translated',
                additional_uniqueness=(
                    dict(
                        app_label='foo_bar_app',
                        model_name='FooBarModel',
                        field_name='translated_slug',
                    ),
                ),
            )

    But Note:
          The field set `unique=True`, but the database level will only deny
          create non-unique slugs, if *all* translations are the same!
          So be careful if you use bulk create/update with not unique data!
          See Tests.
    """

    def __init__(
        self,
        *args,
        populate_from: str = None,
        unique=True,
        additional_uniqueness: tuple[dict] | None = None,
        **kwargs,
    ):
        self.populate_from = populate_from
        self.additional_uniqueness = additional_uniqueness

        kwargs['blank'] = True
        super().__init__(*args, unique=unique, **kwargs)
        assert self.blank is True, 'TranslationSlugField must always set blank=True !'

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['unique'] = self.unique
        kwargs['additional_uniqueness'] = self.additional_uniqueness
        return name, path, args, kwargs

    def create_slug(self, model_instance, add):
        slug_translations = getattr(model_instance, self.attname)
        assert isinstance(
            slug_translations, (FieldTranslation, dict)
        ), f'Unexpected type: {type(slug_translations).__name__}'

        populate_translations = getattr(model_instance, self.populate_from)
        assert isinstance(
            populate_translations, (FieldTranslation, dict)
        ), f'Unexpected type: {type(populate_translations).__name__}'

        for lang_code, _lang_name in self.languages:
            source_text = slug_translations.get(lang_code) or populate_translations.get(lang_code)
            if source_text:
                slug = get_unique_translation_slug(
                    model_instance=model_instance,
                    attr_name=self.attname,
                    source_text=source_text,
                    lang_code=lang_code,
                    additional_uniqueness=self.additional_uniqueness,
                )
                assert slug, f'Can not find a slug from {source_text=}'
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
            translation.get_language(),  # equal to current locale of user
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
            translation_codes[field.name] = field.languages

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

        def patch_fieldnames(fieldnames) -> tuple[str, ...]:
            return tuple(f'get_{field}' if field in translation_fields else field for field in fieldnames)

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


def remove_empty_translations(translations: dict | FieldTranslation) -> FieldTranslation:
    """
    Remove all empty/None from a FieldTranslation, e.g.:

    >>> remove_empty_translations({'de-de': 'Hallo', 'en': 'Hello', 'es':'', 'mx': None})
    FieldTranslation({'de-de': 'Hallo', 'en': 'Hello'})
    """
    filtered = {lang_code: text for lang_code, text in translations.items() if text}
    return FieldTranslation(filtered)


def merge_translations(
    translations1: dict | FieldTranslation, translations2: dict | FieldTranslation
) -> FieldTranslation:
    """
    Merge two FieldTranslation and ignore all empty/None values, e.g.:

    >>> merge_translations({'de': 'Hallo', 'en': '', 'es': 'Hola'}, {'de': '', 'es': 'HOLA'})
    FieldTranslation({'de': 'Hallo', 'es': 'HOLA'})
    """
    merged = remove_empty_translations(translations1)
    merged.update(remove_empty_translations(translations2))
    return FieldTranslation(merged)


def validate_unique_translations(*, ModelClass, instance, field_name, translated_value) -> None:
    """
    Deny creating non-unique translation: Creates ValidationError with change list search for doubled entries.
    Useable for Form/Model clean methods.
    See: bx_django_utils_tests.test_app.admin.TranslatedSlugTestModelForm()
    """
    if not translated_value:
        raise ValidationError({'translated_name': _('At least one translation is required.')})

    q_filters = Q()
    for lang_code, value in translated_value.items():
        if value:
            q_filters |= Q(**{f'{field_name}__{lang_code}': value})

    if not q_filters:
        raise ValidationError({field_name: _('At least one translation is required.')})

    qs = ModelClass.objects.filter(q_filters)
    if instance and (own_pk := instance.pk):
        qs = qs.exclude(pk=own_pk)

    if other_instance := qs.first():
        url = admin_change_url(instance=other_instance)
        msg = mark_safe(
            _('A <a href="%(url)s">other %(model_name)s</a> with one of these translation already exists!')
            % {
                'url': url,
                'model_name': ModelClass._meta.verbose_name_plural,
            }
        )
        raise ValidationError({field_name: msg})


def make_unique(*args) -> tuple:
    """
    Flat args and remove duplicate entries while keeping the order intact.

    >>> make_unique(['de', 'de-de'], 'en', ('en', 'en-gb'), 'de', ['en-gb', 'en-gb', 'en-int'])
    ('de', 'de-de', 'en', 'en-gb', 'en-int')
    """
    args = [[args] if isinstance(args, str) else args for args in args]
    entries = tuple(chain.from_iterable(args))
    return tuple(sorted(set(entries), key=entries.index))


def expand_languages_codes(languages_codes) -> list:
    """
    Build a complete list if language code with and without dialects.

    >>> expand_languages_codes(languages_codes=['de'])
    ['de', 'de-de']
    >>> expand_languages_codes(languages_codes=['en-us', 'en-gb'])
    ['en-us', 'en-gb', 'en']
    >>> expand_languages_codes(languages_codes=['de', 'en-us', 'en-gb'])
    ['de', 'en-us', 'en-gb', 'de-de', 'en']
    """
    assert isinstance(languages_codes, (list, tuple)), f'No list/tuple: {languages_codes=}'
    expanded = list(languages_codes)
    for code in languages_codes:
        if '-' in code:
            code = code.split('-')[0]
        else:
            code = f'{code}-{code}'
        if code not in expanded:
            expanded.append(code)
    return expanded


def get_user_priorities(existing_codes) -> tuple:
    """
    Collect usable language codes the current user
    """
    user_codes = []
    if dj_language := translation.get_language():
        for user_code in expand_languages_codes(languages_codes=[dj_language]):
            if user_code in existing_codes:
                user_codes.append(user_code)

            for code in existing_codes:
                if code.startswith(user_code):
                    user_codes.append(code)
    return make_unique(user_codes)


def user_language_priorities(fallback_codes, existing_codes) -> tuple:
    """
    Returns the order in which to attempt resolving translations of a FieldTranslation model field.
    """
    return make_unique(
        *get_user_priorities(existing_codes),  # Lookup user preferred language with and without dialect first
        *fallback_codes,  # use fallback
        *existing_codes,  # at the end: try any existing language
    )
