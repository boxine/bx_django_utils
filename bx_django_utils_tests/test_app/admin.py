from django.contrib import admin

from bx_django_utils.admin_utils.filters import ExistingCountedListFilter
from bx_django_utils_tests.test_app.admin_filters_demo import NotAllSimpleListFilterDemo
from bx_django_utils_tests.test_app.models import ColorFieldTestModel, CreateOrUpdateTestModel


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
