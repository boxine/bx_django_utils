from django.contrib import admin

from bx_django_utils.admin_extra_views.registry import extra_view_registry


class ExtraViewAdminSite(admin.AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)

        extra_app_list = extra_view_registry.get_app_list(request)
        app_list.extend(extra_app_list)

        return app_list
