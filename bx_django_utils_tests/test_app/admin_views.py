"""
    Just a DEMO for bx_django_utils.admin_extra_views
"""
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView, View

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta, PseudoApp
from bx_django_utils.admin_extra_views.registry import register_admin_view
from bx_django_utils.feature_flags.admin_views import ManageFeatureFlagsBaseView
from bx_django_utils.generic_model_filter.admin_views import GenericModelFilterBaseView
from bx_django_utils_tests.test_app.feature_flags import bar_feature_flag, foo_feature_flag


def only_john_can_access(request):
    user: User = request.user
    if user.is_superuser:
        return True
    if user.username == 'john':
        return True
    else:
        return False


pseudo_app1 = PseudoApp(meta=AdminExtraMeta(name='Pseudo App 1'))
pseudo_app2 = PseudoApp(meta=AdminExtraMeta(name='Pseudo App 2'))


@register_admin_view(pseudo_app=pseudo_app1)
class DemoView1(AdminExtraViewMixin, TemplateView):
    meta = AdminExtraMeta(name='Demo View 1')
    template_name = 'admin_extra_views/demo1.html'

    def get_context_data(self, **context):
        context = super().get_context_data(**context)
        context['content'] = 'Just the demo view 1'
        return context


@register_admin_view(pseudo_app=pseudo_app1)
class DemoView2(AdminExtraViewMixin, View):
    meta = AdminExtraMeta(name='Demo View 2')

    def get(self, request):
        return HttpResponse('Just the demo view 2')


@register_admin_view(pseudo_app=pseudo_app2)
class DemoView3(AdminExtraViewMixin, View):
    meta = AdminExtraMeta(
        name='Demo View 3',
        conditions={only_john_can_access},  # Note: pseudo_app2 conditions will be added!
    )

    def get(self, request):
        url = reverse(self.meta.url_name)
        return HttpResponse(f'Just the demo view at {url!r}')


#####################################################################################
# Feature Flags DEMO

manage_flags_app = PseudoApp(
    meta=AdminExtraMeta(
        name=_('Feature Flags'),
        app_label='feature_flags',
        # Set your needed conditions here!
    )
)


@register_admin_view(pseudo_app=manage_flags_app)
class ManageFeatureFlagsAdminExtraView(ManageFeatureFlagsBaseView):
    pass


@register_admin_view(pseudo_app=manage_flags_app)
class FeatureFlagsInfoView(AdminExtraViewMixin, View):
    """
    Just display the states of the demo feature flags
    """

    meta = AdminExtraMeta(name='Feature Flags values DEMO')

    def get(self, request):
        messages.info(self.request, f'Demo Feature "Foo" state: {foo_feature_flag.state.name}')
        messages.info(self.request, f'Demo Feature "Bar" state: {bar_feature_flag.state.name}')
        url = reverse('admin:index')
        return HttpResponseRedirect(url)


#####################################################################################
# GenericModelFilter DEMO


generic_model_filter_app = PseudoApp(meta=AdminExtraMeta(name='Generic Model Filter'))


@register_admin_view(pseudo_app=generic_model_filter_app)
class GenericModelFilterAdminExtraView(GenericModelFilterBaseView):
    pass
