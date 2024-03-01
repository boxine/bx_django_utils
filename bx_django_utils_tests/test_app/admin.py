from django import forms
from django.contrib import admin
from django.contrib.admin.models import LogEntry

from bx_django_utils.admin_utils.filters import ExistingCountedListFilter
from bx_django_utils.translation import TranslationFieldAdmin, validate_unique_translations
from bx_django_utils_tests.test_app.admin_filters_demo import NotAllSimpleListFilterDemo
from bx_django_utils_tests.test_app.models import (
    ColorFieldTestModel,
    CreateOrUpdateTestModel,
    TranslatedModel,
    TranslatedSlugTestModel,
    ValidateLengthTranslations,
)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_id', 'change_message')
    list_filter = ('action_flag', 'user', 'content_type')


class NameListFilter(ExistingCountedListFilter):
    title = 'name'
    parameter_name = 'name'
    model_field_name = 'name'


class SlugListFilter(ExistingCountedListFilter):
    title = 'slug'
    parameter_name = 'slug'
    model_field_name = 'slug'


@admin.register(CreateOrUpdateTestModel)
class CreateOrUpdateTestModelAdmin(admin.ModelAdmin):
    list_display = ('human_create_dt', 'human_update_dt', 'name', 'slug')
    list_display_links = ('name', 'slug')
    readonly_fields = ('create_dt', 'update_dt')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = (NotAllSimpleListFilterDemo, NameListFilter, SlugListFilter)


@admin.register(ColorFieldTestModel)
class ColorFieldTestModelAdmin(admin.ModelAdmin):
    list_display = ('required_color', 'optional_color')


@admin.register(TranslatedModel)
class TranslatedModelAdmin(TranslationFieldAdmin):
    list_display = ['translated', 'translated_multiline', 'not_translated']
    list_display_links = ['translated', 'translated_multiline']


class TranslatedSlugTestModelForm(forms.ModelForm):
    """
    Demonstrate the usage of validate_unique_translations()
    """

    def clean(self):
        cleaned_data = super().clean()

        validate_unique_translations(
            ModelClass=TranslatedSlugTestModel,
            instance=self.instance,
            field_name='translated',
            translated_value=cleaned_data.get('translated'),
        )

        return cleaned_data

    class Meta:
        model = TranslatedSlugTestModel
        exclude = ()


@admin.register(TranslatedSlugTestModel)
class TranslatedSlugTestModelAdmin(TranslationFieldAdmin):
    form = TranslatedSlugTestModelForm
    list_display = ['translated', 'translated_slug']


@admin.register(ValidateLengthTranslations)
class ValidateLengthTranslationsModelAdmin(TranslationFieldAdmin):
    list_display = ['translated', 'translated_slug']
