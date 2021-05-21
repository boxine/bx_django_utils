from django.contrib import admin

from bx_django_utils.approve_workflow.admin import BaseApproveModelAdmin
from bx_django_utils.approve_workflow.forms import PublishAdminForm
from bx_django_utils_tests.approve_workflow_test_app.models import ApproveTestModel, RelatedApproveTestModel


class RelatedApproveTestModelInline(admin.StackedInline):
    form = PublishAdminForm  # Activate models REQUIRED_FIELDS_PUBLIC on approve
    model = RelatedApproveTestModel
    exclude = ('blocked',)
    extra = 0


@admin.register(ApproveTestModel)
class ApproveTestModelAdmin(BaseApproveModelAdmin):
    inlines = (RelatedApproveTestModelInline,)
