from collections.abc import Iterator

from django.urls import reverse

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta
from bx_django_utils.admin_extra_views.registry import extra_view_registry


def reverse_admin_extra_view(view_class) -> str:
    """
    Get the URL of a Admin Extra View, e.g.: url=reverse_admin_extra_view(YouAdminExtraView)
    """
    assert issubclass(view_class, AdminExtraViewMixin)
    assert isinstance(view_class.meta, AdminExtraMeta)
    url = reverse(view_class.meta.url_name)
    return url


def iter_admin_extra_views_urls() -> Iterator[str]:
    """
    Iterate over all registered admin extra view urls.
    """
    for view_class in extra_view_registry:
        url = reverse_admin_extra_view(view_class)
        yield url
