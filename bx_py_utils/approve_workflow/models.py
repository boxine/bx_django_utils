import logging
import uuid

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from bx_py_utils.models.timetracking import TimetrackingBaseModel


logger = logging.getLogger(__name__)


class BaseApproveModel(TimetrackingBaseModel):
    """
    Base model class for approve models *and* this relation models.
    """
    id = models.UUIDField(
        # The internal primary key
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('BaseApproveModel.pk.verbose_name'),
        help_text=_('BaseApproveModel.pk.help_text')
    )
    is_draft = models.BooleanField(
        # Marks this entry as "draft"
        # Only drafts can be "approve"
        default=True,
        editable=False,
        db_index=True,
        verbose_name=_('BaseApproveModel.is_draft.verbose_name'),
        help_text=_('BaseApproveModel.is_draft.help_text')
    )
    approved = models.OneToOneField(
        # Relation to the "approved" instance
        # Set by self.approve() to the draft instance
        'self',
        on_delete=models.SET_NULL,
        related_name='draft',
        null=True,
        editable=False,
        verbose_name=_('BaseApproveModel.approved.verbose_name'),
        help_text=_('BaseApproveModel.approved.help_text')
    )
    blocked = models.BooleanField(
        default=False,
        verbose_name=_('BaseApproveModel.blocked.verbose_name'),
        help_text=_('BaseApproveModel.blocked.help_text')
    )

    # Fields are required for *approve* instances (should be used in forms):
    REQUIRED_FIELDS_PUBLIC = ()

    def is_approved(self):
        if not self.is_draft:
            # We are the "approved" instance
            return True
        return self.approved_id is not None
    is_approved.short_description = _('Approved')
    is_approved.boolean = True

    def get_missing_field_info(self, ignore_fields=None, extra_fields=None):
        needed_fields = set(self.REQUIRED_FIELDS_PUBLIC)

        if extra_fields:
            needed_fields |= set(extra_fields)

        if ignore_fields:
            needed_fields -= set(ignore_fields)

        missing = []
        for field_name in sorted(needed_fields):
            field = self._meta.get_field(field_name)

            if field.remote_field:
                attname = field_name
                verbose_name = field.name
            else:
                attname = field.get_attname()
                verbose_name = field.verbose_name

            value = getattr(self, attname)
            if field.remote_field and not isinstance(field.remote_field, models.ManyToOneRel):
                # Exists a many2many
                value = value.exists()

            if not value:
                missing.append(
                    (attname, verbose_name, value)
                )
        return missing

    def full_clean(self, **kwargs):
        super().full_clean(**kwargs)
        if not self.is_draft:
            missing = self.get_missing_field_info()
            errors = {}
            for attname, verbose_name, value in missing:
                errors[attname] = ValidationError(
                    _('This field cannot be blank.'),
                    code='blank'
                )
            if errors:
                raise ValidationError(errors)

    def _copy_normal_fields(self, approve_instance):
        """
        Just assign all normal field values from draft to approve version.
        """
        raise NotImplementedError

    def _copy_relations(self, approve_instance):
        """
        Assign relations from draft to approve version.
        """
        raise NotImplementedError

    def approve(self, **values):
        """
        1. validate that draft in complete filled
        2. Create/update a approve instance with all data from the draft
        """
        logger.debug('Approve %s', self)

        if not self.is_draft:
            raise ValidationError('Only drafts can be approve!')

        if self.blocked:
            raise ValidationError('Blocked entries can not approved!')

        # Check validation before creating the approve version
        self.full_clean()

        with transaction.atomic():
            if self.approved is None:
                approve_instance = self.__class__(
                    is_draft=False,
                )
            else:
                approve_instance = self.approved

            assert approve_instance.is_draft is False

            for key, value in values.items():
                setattr(approve_instance, key, value)

            # "normal" field values can be assigned before a new approve instance
            # has been saved and has a primary key
            self._copy_normal_fields(approve_instance)

            # Transfer date times:
            approve_instance.create_dt = self.create_dt
            approve_instance.update_dt = self.update_dt

            # Save the instance to set a primary key
            # PK is needed to assign relations
            approve_instance.save(
                # Maybe relations are needed -> skip validation
                # validation will be done later, see below
                call_clean=False,
                update_dt=False  # Keep date time from draft
            )

            # Assign all relation data
            self._copy_relations(approve_instance)

            # If fields are missing or validation failed
            # -> raise and error and abort the transaction
            approve_instance.full_clean()

            if self.approved_id is not approve_instance.pk:
                # Save approve instance to draft version
                self.approved_id = approve_instance.pk
                self.save(
                    update_fields=('approved_id',),
                    update_dt=False  # Keep date time from draft
                )

        logger.info('%s was approved to %s', self, approve_instance)
        return approve_instance

    def save(self, call_clean=True, **kwargs):
        if call_clean:
            # The approve version should be validated
            self.full_clean()

        return super().save(**kwargs)

    def __repr__(self):
        if self.is_draft:
            info = 'draft'
        else:
            info = 'approved'
        return f'<{self.__class__.__name__} pk:{self.pk} ({info})>'

    def __str__(self):
        return self.__repr__()

    class Meta:
        default_permissions = ('add', 'change', 'delete', 'view', 'approve')  # Add 'approve'
        abstract = True


class BaseApproveWorkflowModel(BaseApproveModel):
    """
    Base model for approve workflow models.
    Don't used this for approve relation models!
    """
    ready_to_approve = models.BooleanField(
        # Marks when it's ready to approve
        default=False,
        null=False,
        blank=True,
        verbose_name=_('BaseApproveWorkflowModel.ready_to_approve.verbose_name'),
        help_text=_('BaseApproveWorkflowModel.ready_to_approve.help_text')
    )

    def approve(self, **values):
        if not self.is_draft:
            raise ValidationError('Only drafts can be approve!')

        if not self.ready_to_approve:
            logger.warning('Not ready to approve: pk:%r model:%s', self.pk, type(self).__name__)

        with transaction.atomic():
            # Remove the "ready" flag for next edit:
            self.ready_to_approve = False
            self.save(
                update_fields=('ready_to_approve',),
                update_dt=False  # Keep date time from draft
            )

            approve_instance = super().approve(**values)

            # self._copy_normal_fields() should not copy the "ready" flag:
            assert not approve_instance.ready_to_approve

        return approve_instance

    def __repr__(self):
        if self.is_draft:
            if self.ready_to_approve:
                info = 'draft, ready to approve'
            else:
                info = 'draft, not ready'
        else:
            info = 'approved'
        return f'<{self.__class__.__name__} pk:{self.pk} ({info})>'

    def __str__(self):
        return self.__repr__()

    class Meta(BaseApproveModel.Meta):
        abstract = True
