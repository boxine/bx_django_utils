from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta
from bx_django_utils.feature_flags.data_classes import FeatureFlag, State


class ManageFeatureFlagsForm(forms.Form):
    """"""  # noqa - don't add in README

    cache_key = forms.ChoiceField(
        choices=((instance.cache_key, instance.human_name) for instance in FeatureFlag.values())
    )
    new_value = forms.ChoiceField(choices=State.choices)


class ManageFeatureFlagsBaseView(AdminExtraViewMixin, FormView):
    """
    Base admin extra view to manage all existing feature flags in admin.

    Intended to register this view yourself and set/check the user permissions
    according to your own requirements.
    """

    meta = AdminExtraMeta(name=_('Manage Feature Flags'), app_label='manage')
    template_name = 'admin_extra_views/manage_feature_flags.html'
    form_class = ManageFeatureFlagsForm

    def get_context_data(self, **context):
        feature_flags = []
        for instance in FeatureFlag.values():
            feature_flags.append(
                dict(
                    cache_key=instance.cache_key,
                    human_name=instance.human_name,
                    description=instance.description,
                    state=instance.state,
                    initial_state=instance.initial_state,
                    opposite_state=instance.opposite_state,
                )
            )
        if not feature_flags:
            messages.info(self.request, _('No feature flags currently registered'))
        context['feature_flags'] = feature_flags
        return super().get_context_data(**context)

    def form_valid(self, form):
        cache_key = form.cleaned_data['cache_key']
        new_value_str = form.cleaned_data['new_value']

        new_sate_value = int(new_value_str)
        new_state = State(new_sate_value)

        feature_flag = FeatureFlag.get_by_cache_key(cache_key)
        if feature_flag.opposite_state != new_state:
            messages.error(
                self.request,
                f'Current "{feature_flag.human_name}" state is already: {feature_flag.state.name}',
            )
        else:
            feature_flag.set_state(new_state)
            messages.success(
                self.request, f'Set "{feature_flag.human_name}" state to {feature_flag.state.name}'
            )
        return HttpResponseRedirect('.')
