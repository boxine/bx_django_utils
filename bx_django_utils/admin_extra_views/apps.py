from django.apps import AppConfig

from bx_django_utils.admin_extra_views.autodiscover import autodiscover_admin_views


class AdminExtraViewsAppConfig(AppConfig):
    """
    App config to auto discover all extra views.
    """

    name = 'bx_django_utils.admin_extra_views'
    verbose_name = "Admin Extra views"

    def ready(self):
        autodiscover_admin_views()

        # Register system checks:
        from bx_django_utils.admin_extra_views.checks import admin_extra_views_check  # noqa
