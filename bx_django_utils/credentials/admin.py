from django.contrib import admin

from bx_django_utils.credentials.forms import CredentialForm
from bx_django_utils.credentials.models import Credential


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    """
    Model Admin for manage Credential entries that never display a plaintext secret.
    """

    form = CredentialForm
    list_display = ['key', 'secret_anonymized']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('key')
