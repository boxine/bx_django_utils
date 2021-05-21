from django.contrib import admin

from bx_django_utils_tests.test_app.models import CreateOrUpdateTestModel


@admin.register(CreateOrUpdateTestModel)
class CreateOrUpdateTestModelAdmin(admin.ModelAdmin):
    list_display = ('human_create_dt', 'human_update_dt', 'name', 'slug')
    list_display_links = ('name', 'slug')
    readonly_fields = ('create_dt', 'update_dt')
