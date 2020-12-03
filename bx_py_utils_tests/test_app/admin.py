from django.contrib import admin

from bx_py_utils_tests.test_app.models import CreateOrUpdateTestModel


@admin.register(CreateOrUpdateTestModel)
class CreateOrUpdateTestModelAdmin(admin.ModelAdmin):
    readonly_fields = ('create_dt', 'update_dt')
