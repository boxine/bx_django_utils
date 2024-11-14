from django import forms
from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta
from bx_django_utils.feature_flags.data_classes import FeatureFlag
from bx_django_utils.feature_flags.models import FeatureFlagModel
from bx_django_utils.feature_flags.state import State


def get_feature_flag_choices():
    choices = ((instance.cache_key, instance.human_name) for instance in FeatureFlag.values())
    return choices


class ManageFeatureFlagsForm(forms.Form):
    """"""  # noqa - don't add in README

    cache_key = forms.ChoiceField(
        choices=get_feature_flag_choices,  # Assign lazy
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
        content_type_id = ContentType.objects.get_for_model(FeatureFlagModel).id
        log_entry_qs = LogEntry.objects.order_by('action_time').filter(content_type_id=content_type_id)
        feature_flags = []
        for instance in FeatureFlag.values():
            cache_key = instance.cache_key
            human_name = instance.human_name

            # We didn't set `object_id` in the past. So we must add the ugly `change_message` fallback:
            last_change_qs = log_entry_qs.filter(Q(object_id=cache_key) | Q(change_message__contains=human_name))

            feature_flags.append(
                dict(
                    cache_key=cache_key,
                    human_name=human_name,
                    description=instance.description,
                    state=instance.state,
                    initial_state=instance.initial_state,
                    opposite_state=instance.opposite_state,
                    last_change=last_change_qs.last(),
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
            change_message = f'Set "{feature_flag.human_name}" to {feature_flag.state.name}'

            if hasattr(feature_flag, '_cache_duration'):
                eta = int(feature_flag._cache_duration.total_seconds())
                change_message += f' (will take up to {eta} seconds to take full effect)'

            # Create a LogEntry for this action:
            content_type_id = ContentType.objects.get_for_model(FeatureFlagModel).id
            log_entry = LogEntry.objects.log_action(
                user_id=self.request.user.id,
                content_type_id=content_type_id,
                action_flag=CHANGE,
                change_message=f'Changed feature flag "{feature_flag.human_name}"',
                object_id=cache_key,
                object_repr=change_message,  # Rendered in Django log list on index page!
            )
            log_entry.full_clean()

            messages.success(self.request, change_message)

        return HttpResponseRedirect('.')
