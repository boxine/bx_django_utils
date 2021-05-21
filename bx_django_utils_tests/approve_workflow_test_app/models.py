import logging

from django.db import models

from bx_django_utils.approve_workflow.models import BaseApproveModel, BaseApproveWorkflowModel


logger = logging.getLogger(__name__)


class ApproveTestModel(BaseApproveWorkflowModel):
    """
    Example implementation of a ApproveWorkflowModel with a relation.
    Used in tests.
    """
    name = models.CharField(
        max_length=128,
        verbose_name='The Name',
        help_text='This is always needed field',
    )
    title = models.CharField(
        max_length=128,
        blank=True,
        verbose_name='A Title',
        help_text='This is only needed to approve this entry'
    )

    # Fields are required for *draft* instances (used in admin model form):
    REQUIRED_FIELDS_DRAFT = ()

    # Fields are required for *approve* instances (used in admin model form):
    REQUIRED_FIELDS_PUBLIC = ('title',)

    def _copy_normal_fields(self, approve_instance):
        """
        Just assign all normal field values from draft to approve version.
        """
        approve_instance.name = self.name
        approve_instance.title = self.title

    def _copy_relations(self, approve_instance):
        """
        Assign relations from draft to approve version.
        """
        draft_relations = self.relations.all()
        seen_pks = []
        for draft_relation in draft_relations:
            seen_pks.append(draft_relation.pk)
            approved_relation = draft_relation.approve(main_entry_id=approve_instance.pk)
            seen_pks.append(approved_relation.pk)

        # Remove obsolete relations:
        cleanup_qs = RelatedApproveTestModel.objects.filter(
            main_entry=approve_instance
        ).exclude(pk__in=seen_pks)
        delete_count = cleanup_qs.delete()[0]
        if delete_count:
            logger.debug('delete %i relations', delete_count)


class RelatedApproveTestModel(BaseApproveModel):
    relation_name = models.CharField(
        max_length=128,
        verbose_name='The Name',
        help_text='This is always needed field',
    )
    relation_title = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name='A Title',
        help_text='This is only needed to approve this entry'
    )

    main_entry = models.ForeignKey(
        ApproveTestModel,
        on_delete=models.CASCADE,
        related_name='relations',
    )

    # Fields are required for *draft* instances (used in admin model form):
    REQUIRED_FIELDS_DRAFT = ()

    # Fields are required for *approve* instances (used in admin model form):
    REQUIRED_FIELDS_PUBLIC = ('relation_title',)

    def _copy_normal_fields(self, approve_instance):
        """
        Just assign all normal field values from draft to approve version.
        """
        approve_instance.relation_name = self.relation_name
        approve_instance.relation_title = self.relation_title

    def _copy_relations(self, approve_instance):
        """
        Assign relations from draft to approve version.
        """
        approve_instance.main_entry = self.main_entry

    def approve(self, main_entry_id):
        approve_instance = super().approve(
            # Publish and attach to given main_entry:
            main_entry_id=main_entry_id
        )

        return approve_instance
