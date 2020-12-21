from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bx_py_utils.templatetags.humanize_time import human_duration


class TimetrackingBaseModel(models.Model):
    """
    Abstract base model that will automaticly set create/update Datetimes.

    Using a DateTimeField with auto_now/auto_now_add is not a good idea.
    Because you can't easy disable these auto behaviour.

    Here you can pass update_dt=False to save() method.
    """
    create_dt = models.DateTimeField(
        blank=True, null=True, editable=False,
        verbose_name=_('ModelTimetrackingMixin.create_dt.verbose_name'),
        help_text=_('ModelTimetrackingMixin.create_dt.help_text')
    )
    update_dt = models.DateTimeField(
        blank=True, null=True, editable=False,
        verbose_name=_('ModelTimetrackingMixin.update_dt.verbose_name'),
        help_text=_('ModelTimetrackingMixin.update_dt.help_text')
    )

    def human_create_dt(self):
        return human_duration(self.create_dt)
    human_create_dt.short_description = _('ModelTimetrackingMixin.create_dt.verbose_name')
    human_create_dt.admin_order_field = 'create_dt'

    def human_update_dt(self):
        return human_duration(self.update_dt)
    human_update_dt.short_description = _('ModelTimetrackingMixin.update_dt.verbose_name')
    human_update_dt.admin_order_field = 'update_dt'

    def save(self, update_dt=True, **kwargs):
        if update_dt:
            if 'update_fields' in kwargs:
                update_fields = list(kwargs['update_fields'])
            else:
                update_fields = None

            self.update_dt = timezone.now()
            if update_fields is not None:
                assert 'update_dt' not in update_fields
                update_fields.append('update_dt')

            if self.create_dt is None:
                self.create_dt = self.update_dt
                if update_fields is not None:
                    assert 'create_dt' not in update_fields
                    update_fields.append('create_dt')

            if update_fields is not None:
                kwargs['update_fields'] = update_fields

        super().save(**kwargs)

    class Meta:
        abstract = True
