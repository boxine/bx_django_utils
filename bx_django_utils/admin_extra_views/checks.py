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
                    msg=f'Admin extra views URL reverse error with {view_class.__name__!r}',
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
                msg='No admin extra views registered!',
                id='admin_extra_views.W001',
            )
        )

    for pseudo_app in extra_view_registry.pseudo_apps:
        admin_site = pseudo_app.admin_site
        if not isinstance(admin_site, ExtraViewAdminSite):
            errors.append(
                Error(
                    msg=(
                        f'Pseudo app {pseudo_app.meta.name!r} error:'
                        f' Admin site {admin_site.__class__.__name__!r}'
                        ' is not a instance of ExtraViewAdminSite!'
                    ),
                    hint='Use CustomAdminConfig or add "site" to PseudoApp definition',
                    id='admin_extra_views.E002',
                )
            )

    return errors
