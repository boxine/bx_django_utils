from django.contrib.admin.sites import DefaultAdminSite
from django.core.checks import Error, Warning, register
from django.urls import NoReverseMatch, reverse

from bx_django_utils.admin_extra_views.registry import extra_view_registry
from bx_django_utils.admin_extra_views.site import ExtraViewAdminSite


class _ByPassConditions:
    def __enter__(self):
        extra_view_registry._by_pass_conditions = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        extra_view_registry._by_pass_conditions = False


@register()
def admin_extra_views_check(app_configs, **kwargs):
    errors = []

    view_count = 0
    for view_class in extra_view_registry:
        try:
            url = reverse(view_class.meta.url_name)
        except NoReverseMatch as err:
            errors.append(
                Error(
                    'Admin extra views URL reverse error',
                    hint='Have you include "extra_view_registry.get_urls()" to your urls.py ?',
                    obj=err,
                    id='admin_extra_views.E001',
                )
            )
        else:
            assert url
            view_count += 1

    if view_count == 0:
        errors.append(
            Warning(
                'No admin extra views registered!',
                id='admin_extra_views.W001',
            )
        )

    site = DefaultAdminSite()
    if not isinstance(site, ExtraViewAdminSite):
        errors.append(
            Warning(
                'DefaultAdminSite is not a instance of ExtraViewAdminSite!',
                hint='Have you used admin_extra_views.admin_config.CustomAdminConfig ?',
                id='admin_extra_views.W002',
            )
        )

    return errors
