from django.views.generic import RedirectView

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.utils import reverse_admin_extra_view


class Redirect2AdminExtraView(RedirectView):
    """
    Redirect to a Admin Extra Views.
    """

    admin_view = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        assert self.admin_view is not None
        if not issubclass(self.admin_view, AdminExtraViewMixin):
            raise ValueError(f'Admin view {self.admin_view} must subclass AdminExtraViewMixin.')

    def get_redirect_url(self, *args, **kwargs):
        url = reverse_admin_extra_view(view_class=self.admin_view)
        return url
