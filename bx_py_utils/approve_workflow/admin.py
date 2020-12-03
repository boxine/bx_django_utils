import logging

from django.contrib import admin, messages
from django.contrib.auth import get_permission_codename
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from bx_py_utils.approve_workflow.constants import POST_KEY_APPROVE
from bx_py_utils.approve_workflow.forms import PublishAdminForm


logger = logging.getLogger(__name__)


class BaseApproveModelAdmin(admin.ModelAdmin):
    form = PublishAdminForm  # Activate models REQUIRED_FIELDS_PUBLIC on approve
    change_form_template = 'approve_workflow/change_form.html'
    readonly_fields = (
        'approved',
        'is_draft', 'ready_to_approve',
        'create_dt', 'update_dt'
    )
    list_display = (
        '__str__',
        'approved',
        'is_draft', 'ready_to_approve',
        'create_dt', 'update_dt'
    )

    def has_approve_permissions(self, user):
        opts = self.opts
        codename = get_permission_codename('approve', opts)
        perm = f'{opts.app_label}.{codename}'
        has_permission = user.has_perm(perm)
        if not has_permission:
            logger.debug('User %r has not %r permissions', user.pk, perm)
        return has_permission

    def render_change_form(self, request, context, obj=None, **kwargs):
        if obj is None or not obj.is_draft:
            show_approve = False
        else:
            # Display "Approve" button in submit line if user has approve permissions
            show_approve = self.has_approve_permissions(user=request.user)

        if obj is None or obj.is_draft:
            show_approve_warning = False
        else:
            # Use changed the approved version -> Display warning about this
            show_approve_warning = True

        context.update({
            'show_approve_warning': show_approve_warning,
            'show_approve': show_approve,
        })
        return super().render_change_form(request, context, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)

        # Override form when pressing approve button
        if POST_KEY_APPROVE in request.POST and obj:
            class ApproveCheckForm(Form):
                def clean(self):
                    if self.cleaned_data['blocked']:
                        raise ValidationError({'blocked': 'Blocked item cannot be approved!'})
                    return super().clean()

            return ApproveCheckForm

        return Form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if POST_KEY_APPROVE in request.POST:
            # save instance, because we can only approve after relations are saved, too.
            logger.debug('to_approve=%r', obj)
            self.to_approve = obj

    def _approve(self, request, obj):
        can_approve = self.has_approve_permissions(user=request.user)
        if not can_approve:
            raise PermissionError('User can not approve')

        ready_to_approve = obj.ready_to_approve
        approved = obj.approve()
        logger.debug('%r approved to %r', obj, approved)
        if not ready_to_approve:
            messages.warning(request, _('Warning: "Ready to Approve" flag was not set!'))
        self.message_user(request, _('%s was approved') % approved, messages.SUCCESS)

    def _changeform_view(self, request, object_id, form_url, extra_context):
        """
        It's a little bit tricky to approve a instance, because we can only
        approve a instance after it was saved and after all relations was saved!
        """
        self.to_approve = None
        response = super()._changeform_view(request, object_id, form_url, extra_context)
        if self.to_approve is not None:
            # model and all relations was saved and self.save_model() has set self.to_approve
            self._approve(request, obj=self.to_approve)

        return response
