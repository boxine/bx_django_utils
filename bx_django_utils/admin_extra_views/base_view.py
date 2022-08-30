import logging

from django.core.exceptions import PermissionDenied

from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta


logger = logging.getLogger(__name__)


class AdminExtraViewMixin:
    meta: AdminExtraMeta = None  # Must be set by view

    def dispatch(self, request, *args, **kwargs):
        for condition_func in self.meta.conditions:
            if not condition_func(request):
                logger.warning(
                    'User (pk:%r) did not pass %r for %r',
                    request.user.pk,
                    condition_func.__name__,
                    self.__class__.__name__,
                )
                raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
