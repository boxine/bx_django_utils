from collections.abc import Iterator

from django.http import HttpRequest
from django.urls import path, reverse
from django.views import View

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta, PseudoApp


class AdminExtraViewRegistry:
    """
    Hold all information about all admin extra views to expand urls and admin app list.
    """

    def __init__(self):
        self.pseudo_apps = set()

    def add_view(self, pseudo_app: PseudoApp, view_class: type[AdminExtraViewMixin | View]) -> None:
        """
        Collect all admin extra views. Called by our @register_admin_view() decorator.
        """
        if not issubclass(view_class, AdminExtraViewMixin):
            raise ValueError('Wrapped class must subclass AdminExtraViewMixin.')

        if not isinstance(view_class.meta, AdminExtraMeta):
            raise ValueError(f'View {view_class} must have a "AdminExtraMeta" instance.')

        view_class.meta.setup_app(pseudo_app)

        pseudo_app.views.append(view_class)
        if pseudo_app not in self.pseudo_apps:
            self.pseudo_apps.add(pseudo_app)

    def get_urls(self) -> list:
        """
        :return: all url patterns for all admin extra views.

        Should be used in urls.py beside the "admin.site.urls" to add all extra views.
        """
        urls = []

        for pseudo_app in self.pseudo_apps:
            for view_class in pseudo_app.views:
                url_pattern = path(
                    view_class.meta.url,
                    view_class.as_view(),
                    name=view_class.meta.url_name,
                )
                urls.append(url_pattern)

        return urls

    def get_app_list(self, request: HttpRequest, app_label=None) -> list:
        """
        :return: The extra views app list, filtered by all conditions

        Should be used in AdminSite.get_app_list() to add all extra views.
        """
        app_list = []
        for pseudo_app in sorted(self.pseudo_apps, key=lambda x: x.meta.name):
            if app_label and pseudo_app.meta.app_label != app_label:
                # User clicked on a Admin app header link. -> List only this one app index.
                # e.g.: Click on "Authentication and Authorization" -> /admin/auth/
                continue

            if not all(cond(request) for cond in pseudo_app.meta.conditions):
                # Don't add the view if the user can't use them
                # Important: This will not deny the access!
                # conditions will be checked in AdminExtraViewMixin.dispatch(), too!
                continue

            models = []
            for view_class in sorted(pseudo_app.views, key=lambda x: x.meta.name):
                if all(cond(request) for cond in view_class.meta.conditions):
                    models.append(
                        {
                            'name': view_class.meta.name,
                            'app_label': view_class.meta.app_label,
                            'admin_url': reverse(view_class.meta.url_name),
                            'view_only': True,
                        }
                    )
            if models:
                app_list.append(
                    {
                        'name': pseudo_app.meta.name,
                        'app_label': pseudo_app.meta.app_label,
                        'models': models,
                    }
                )

        return app_list

    def __iter__(self) -> Iterator[type[AdminExtraViewMixin | View]]:
        """
        Iterate sorted over all registered admin extra view classes.
        """
        for pseudo_app in sorted(self.pseudo_apps, key=lambda x: x.meta.name):
            yield from sorted(pseudo_app.views, key=lambda x: x.meta.name)


extra_view_registry = AdminExtraViewRegistry()


def register_admin_view(*, pseudo_app):
    """
    Decorator to add a normal view as pseudo App/Model to the admin.
    """

    def _model_admin_wrapper(view_class):
        if not isinstance(pseudo_app, PseudoApp):
            raise ValueError('Keyword argument "pseudo_app" must be a PseudoApp instance.')

        extra_view_registry.add_view(pseudo_app, view_class)

        return view_class

    return _model_admin_wrapper
