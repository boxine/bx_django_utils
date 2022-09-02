"""
    Activate "ExtraViewAdminSite" by set this as default admin site
"""
from django.contrib.admin.apps import AdminConfig


class CustomAdminConfig(AdminConfig):
    """
    Change Django Admin Site to ExtraViewAdminSite for the extra views.
    """

    default_site = 'bx_django_utils.admin_extra_views.site.ExtraViewAdminSite'
