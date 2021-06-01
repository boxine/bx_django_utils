import logging
from unittest import mock

from bx_py_utils.test_utils.datetime import parse_dt
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from bx_django_utils.test_utils.datetime import MockDatetimeGenerator
from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from bx_django_utils.test_utils.users import make_minimal_test_user
from bx_django_utils_tests.approve_workflow_test_app.models import ApproveTestModel, RelatedApproveTestModel


class BaseApproveModelTestCase(TestCase):
    @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
    def test_approve(self):
        draft = ApproveTestModel.objects.create(
            id='00000000-0000-0000-0000-000000000001',
            name='v1',
            title='',
        )
        assert draft.is_draft is True
        assert draft.approved is None
        assert draft.is_approved() is False
        assert draft.create_dt == parse_dt('2001-01-01T00:00:00+0000')
        assert draft.update_dt == parse_dt('2001-01-01T00:00:00+0000')
        assert draft.blocked is False
        assert draft.ready_to_approve is False
        assert draft.get_missing_field_info() == [('title', 'A Title', '')]

        # We can't approve with required fields:
        with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs:
            with self.assertRaisesMessage(ValidationError, "{'title': ['This field cannot be blank.']}"):
                draft.approve()

        # Not set "ready_to_approve" generates only a warning:
        assert logs.output == [
            "WARNING:bx_django_utils.approve_workflow.models:Not ready to approve:"
            " pk:UUID('00000000-0000-0000-0000-000000000001') model:ApproveTestModel"
        ]

        # Set a 'title' and check missing fields:
        draft.title = 'v1'
        draft.ready_to_approve = True
        draft.save()
        draft = ApproveTestModel.objects.get(pk=draft.pk)
        assert draft.create_dt == parse_dt('2001-01-01T00:00:00+0000')  # is the same?
        assert draft.update_dt == parse_dt('2002-01-01T00:00:00+0000')  # updated?
        assert draft.get_missing_field_info() == []

        # "blocked" entries can't approve:

        draft.blocked = True
        with self.assertLogs('bx_django_utils', level=logging.DEBUG) as logs:
            with self.assertRaisesMessage(ValidationError, 'Blocked entries can not approved!'):
                draft.approve()
        assert ApproveTestModel.objects.count() == 1  # only one draft exists
        assert logs.output == [
            'DEBUG:bx_django_utils.approve_workflow.models:Approve <ApproveTestModel '
            'pk:00000000-0000-0000-0000-000000000001 (draft, not ready)>',
        ]

        # ready & not blocked -> approve will work:
        draft.blocked = False
        with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs:
            approved = draft.approve()
        assert isinstance(approved, ApproveTestModel)
        assert logs.output == [
            "WARNING:bx_django_utils.approve_workflow.models:Not ready to approve:"
            " pk:UUID('00000000-0000-0000-0000-000000000001') model:ApproveTestModel"
        ]

        # Now we have two entries: The draft and the approve one:
        assert tuple(
            ApproveTestModel.objects.values_list('pk', 'title', 'is_draft').order_by('-is_draft')
        ) == (
            (draft.pk, 'v1', True),
            (approved.pk, 'v1', False)
        )

        # Get fresh versions from database and check:

        approved = ApproveTestModel.objects.get(pk=approved.pk)
        draft = ApproveTestModel.objects.get(pk=draft.pk)

        assert draft.is_draft
        assert not approved.is_draft
        assert draft.approved.pk == approved.pk

        # Both entries are "is_approved" (Used in admin for drafts, too):
        assert draft.is_approved() is True
        assert approved.is_approved() is True

        # Note: After approve the "ready" flag will be removed (for next edit):
        assert draft.ready_to_approve is False
        assert approved.ready_to_approve is False

        assert approved.title == draft.title == 'v1'

        # The Approved version should have the same timestamps:
        assert approved.create_dt == draft.create_dt == parse_dt('2001-01-01T00:00:00+0000')
        assert approved.update_dt == draft.update_dt == parse_dt('2002-01-01T00:00:00+0000')

        # Only drafts can be approved:

        with self.assertRaisesMessage(ValidationError, 'Only drafts can be approve!'):
            approved.approve()

        # Change a field:

        draft.title = 'v2'
        draft.ready_to_approve = True
        draft.save()

        assert tuple(
            ApproveTestModel.objects.values_list('pk', 'title', 'is_draft').order_by('-is_draft')
        ) == (
            (draft.pk, 'v2', True),
            (approved.pk, 'v1', False)
        )

        # Publish again, with ready_to_approve = True -> No warning

        with self.assertLogs('bx_django_utils', level=logging.INFO) as logs:
            approved = draft.approve()
        assert logs.output == [
            'INFO:bx_django_utils.approve_workflow.models:<ApproveTestModel '
            'pk:00000000-0000-0000-0000-000000000001 (draft, not ready)> was approved to '
            f'<ApproveTestModel pk:{approved.pk} (approved)>',
        ]

        assert tuple(
            ApproveTestModel.objects.values_list('pk', 'title', 'is_draft').order_by('-is_draft')
        ) == (
            (draft.pk, 'v2', True),
            (approved.pk, 'v2', False)
        )

        # Get fresh versions from database and check:

        approved = ApproveTestModel.objects.get(pk=approved.pk)
        draft = ApproveTestModel.objects.get(pk=draft.pk)

        assert draft.is_draft
        assert draft.approved.pk == approved.pk
        assert not approved.is_draft

        # Both entries are "is_approved" (Used in admin for drafts, too):
        assert draft.is_approved() is True
        assert approved.is_approved() is True

        # Note: After approve the "ready" flag will be removed (for next edit):
        assert draft.ready_to_approve is False
        assert approved.ready_to_approve is False

        assert approved.title == draft.title == 'v2'

        # Add a relation:

        relation1_draft = RelatedApproveTestModel.objects.create(
            relation_name='relation one v1',
            relation_title=None,
            main_entry=draft,
        )
        relation2_draft = RelatedApproveTestModel.objects.create(
            relation_name='relation two v1',
            relation_title='The Title',
            main_entry=draft,
        )

        assert tuple(
            RelatedApproveTestModel.objects.values_list(
                'main_entry_id', 'relation_name', 'is_draft'
            ).order_by('-is_draft', 'relation_name')
        ) == (
            (draft.pk, 'relation one v1', True),
            (draft.pk, 'relation two v1', True),
        )

        # Can't publish if relations has missing fields, too:

        with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs:
            with self.assertRaisesMessage(ValidationError, "{'relation_title': ['This field cannot be blank.']}"):
                draft.approve()
        assert logs.output == [
            "WARNING:bx_django_utils.approve_workflow.models:Not ready to approve:"
            " pk:UUID('00000000-0000-0000-0000-000000000001') model:ApproveTestModel"
        ]

        assert relation1_draft.approved is None
        relation1_draft.relation_title = 'Now a title set'
        relation1_draft.save()

        # Publish with relations
        draft.title = 'v3'
        draft.ready_to_approve = True
        draft.save()
        assert tuple(
            ApproveTestModel.objects.values_list('pk', 'title', 'is_draft').order_by('-is_draft')
        ) == (
            (draft.pk, 'v3', True),
            (approved.pk, 'v2', False)
        )
        draft.ready_to_approve = True
        with self.assertLogs('bx_django_utils', level=logging.INFO):
            approved = draft.approve()

        assert tuple(
            ApproveTestModel.objects.values_list('pk', 'title', 'is_draft').order_by('-is_draft')
        ) == (
            (draft.pk, 'v3', True),
            (approved.pk, 'v3', False)
        )
        assert tuple(
            RelatedApproveTestModel.objects.values_list(
                'main_entry_id', 'relation_name', 'relation_title', 'is_draft'
            ).order_by('-is_draft', 'relation_name')
        ) == (
            (draft.pk, 'relation one v1', 'Now a title set', True),
            (draft.pk, 'relation two v1', 'The Title', True),
            (approved.pk, 'relation one v1', 'Now a title set', False),
            (approved.pk, 'relation two v1', 'The Title', False),
        )
        relation1_draft = RelatedApproveTestModel.objects.get(pk=relation1_draft.pk)
        relation1_approved = relation1_draft.approved
        assert relation1_approved is not None
        assert relation1_draft.relation_name == relation1_approved.relation_name == 'relation one v1'

        # Change the draft version doesn't touch the approve one:

        relation1_draft.relation_name = 'relation one v2'
        relation1_draft.save()
        relation1_draft = RelatedApproveTestModel.objects.get(pk=relation1_draft.pk)
        assert relation1_draft.approved.relation_name == 'relation one v1'

        # Remove a relation:
        relation2_draft.delete()

        assert tuple(
            RelatedApproveTestModel.objects.values_list(
                'main_entry_id', 'relation_name', 'is_draft'
            ).order_by('-is_draft', 'relation_name')
        ) == (
            (draft.pk, 'relation one v2', True),
            (approved.pk, 'relation one v1', False),
            (approved.pk, 'relation two v1', False),
        )

        # Publish the new relations:

        draft.ready_to_approve = True
        with self.assertLogs('bx_django_utils', level=logging.INFO):
            draft.approve()

        assert tuple(
            RelatedApproveTestModel.objects.values_list(
                'main_entry_id', 'relation_name', 'is_draft'
            ).order_by('-is_draft', 'relation_name')
        ) == (
            (draft.pk, 'relation one v2', True),
            (approved.pk, 'relation one v2', False),
        )


class BaseApproveModelAdminTestCase(HtmlAssertionMixin, TestCase):
    def test_approve(self):
        draft = ApproveTestModel.objects.create(
            id='00000000-0000-0000-0000-000000000001',
            name='v1',
            title='',
        )
        relation_draft = RelatedApproveTestModel.objects.create(
            id='00000000-0000-0000-0000-000000000002',
            relation_name='relation one v1',
            relation_title=None,
            main_entry=draft,
        )
        minimal_test_user = make_minimal_test_user(
            is_staff=True,
            permissions=(
                'approve_workflow_test_app.add_approvetestmodel',
                'approve_workflow_test_app.approve_approvetestmodel',
                'approve_workflow_test_app.change_approvetestmodel',
                'approve_workflow_test_app.delete_approvetestmodel',
                'approve_workflow_test_app.view_approvetestmodel',
                'approve_workflow_test_app.add_relatedapprovetestmodel',
                'approve_workflow_test_app.approve_relatedapprovetestmodel',
                'approve_workflow_test_app.change_relatedapprovetestmodel',
                'approve_workflow_test_app.delete_relatedapprovetestmodel',
                'approve_workflow_test_app.view_relatedapprovetestmodel',
            )
        )
        self.client.force_login(user=minimal_test_user)

        # User sees the test app model:
        response = self.client.get(path='/admin/')
        self.assert_html_parts(response, parts=(
            '<title>Site administration | Django site admin</title>',
            '<a href="/admin/approve_workflow_test_app/approvetestmodel/">Approve test models</a>',
        ))

        url = (
            '/admin/approve_workflow_test_app/approvetestmodel'
            '/00000000-0000-0000-0000-000000000001/change/'
        )
        # User can change the entry and the approve button exists:
        response = self.client.get(url)
        assert response.status_code == 200
        self.assert_html_parts(response, parts=(
            '<input type="submit" value="Save and Approve" name="_approve" class="extra_submit">',
            'value="v1"',
            'value="relation one v1"',
        ))

        # We can save without the REQUIRED_FIELDS_PUBLIC fields:

        response = self.client.post(
            path=url,
            data={
                'name': 'v2',
                'title': '',
                'relations-TOTAL_FORMS': '1',
                'relations-INITIAL_FORMS': '1',
                'relations-MIN_NUM_FORMS': '0',
                'relations-MAX_NUM_FORMS': '1000',
                'relations-0-relation_name': 'relation one v2',
                'relations-0-relation_title': '',
                'relations-0-id': '00000000-0000-0000-0000-000000000002',
                'relations-0-main_entry': '00000000-0000-0000-0000-000000000001',
                'relations-__prefix__-relation_name': '',
                'relations-__prefix__-relation_title': '',
                'relations-__prefix__-id': '',
                'relations-__prefix__-main_entry': '00000000-0000-0000-0000-000000000001',
                '_save': 'Save',
            },
        )
        self.assertRedirects(
            response,
            expected_url='/admin/approve_workflow_test_app/approvetestmodel/',
            fetch_redirect_response=False
        )
        draft = ApproveTestModel.objects.get(pk=draft.pk)
        assert draft.name == 'v2'
        assert draft.approved is None
        relation_draft = RelatedApproveTestModel.objects.get(pk=relation_draft.pk)
        assert relation_draft.relation_name == 'relation one v2'
        assert relation_draft.approved is None

        # We can not approve without the REQUIRED_FIELDS_PUBLIC fields:

        response = self.client.post(
            path=url,
            data={
                'name': 'v3',
                'title': '',
                'relations-TOTAL_FORMS': '1',
                'relations-INITIAL_FORMS': '1',
                'relations-MIN_NUM_FORMS': '0',
                'relations-MAX_NUM_FORMS': '1000',
                'relations-0-relation_name': 'relation one v3',
                'relations-0-relation_title': '',
                'relations-0-id': '00000000-0000-0000-0000-000000000002',
                'relations-0-main_entry': '00000000-0000-0000-0000-000000000001',
                'relations-__prefix__-relation_name': '',
                'relations-__prefix__-relation_title': '',
                'relations-__prefix__-id': '',
                'relations-__prefix__-main_entry': '00000000-0000-0000-0000-000000000001',
                '_approve': 'Save+and+Approve',
            },
        )
        self.assert_html_parts(response, parts=(
            '<input type="submit" value="Save and Approve" name="_approve" class="extra_submit">',
            '<li>This field is required.</li>',
            'value="v3"',
            'value="relation one v3"',
        ))
        # Changes are not saved:
        draft = ApproveTestModel.objects.get(pk=draft.pk)
        assert draft.name == 'v2'
        assert draft.approved is None
        relation_draft = RelatedApproveTestModel.objects.get(pk=relation_draft.pk)
        assert relation_draft.relation_name == 'relation one v2'
        assert relation_draft.approved is None

        # We can approve if we add the REQUIRED_FIELDS_PUBLIC field values:

        with self.assertLogs('bx_django_utils', level=logging.INFO) as logs:
            response = self.client.post(
                path=url,
                data={
                    'name': 'v3',
                    'title': 'title now set',
                    'relations-TOTAL_FORMS': '1',
                    'relations-INITIAL_FORMS': '1',
                    'relations-MIN_NUM_FORMS': '0',
                    'relations-MAX_NUM_FORMS': '1000',
                    'relations-0-relation_name': 'relation one v3',
                    'relations-0-relation_title': 'relation title now set',
                    'relations-0-id': '00000000-0000-0000-0000-000000000002',
                    'relations-0-main_entry': '00000000-0000-0000-0000-000000000001',
                    'relations-__prefix__-relation_name': '',
                    'relations-__prefix__-relation_title': '',
                    'relations-__prefix__-id': '',
                    'relations-__prefix__-main_entry': '00000000-0000-0000-0000-000000000001',
                    '_approve': 'Save+and+Approve',
                },
            )
        logs_output = logs.output

        self.assertRedirects(
            response,
            expected_url='/admin/approve_workflow_test_app/approvetestmodel/',
            fetch_redirect_response=False
        )

        # Changes was saved and approve instances are made:

        draft = ApproveTestModel.objects.get(pk=draft.pk)
        approved = draft.approved
        assert tuple(
            ApproveTestModel.objects.values_list(
                'pk', 'name', 'title', 'is_draft'
            ).order_by('-is_draft')
        ) == (
            (draft.pk, 'v3', 'title now set', True),
            (approved.pk, 'v3', 'title now set', False)
        )
        assert tuple(
            RelatedApproveTestModel.objects.values_list(
                'main_entry_id', 'relation_name', 'relation_title', 'is_draft'
            ).order_by('-is_draft', 'relation_name')
        ) == (
            (draft.pk, 'relation one v3', 'relation title now set', True),
            (approved.pk, 'relation one v3', 'relation title now set', False),
        )
        assert approved is not None
        assert draft.name == approved.name == 'v3'
        assert draft.title == approved.title == 'title now set'

        rel_draft = RelatedApproveTestModel.objects.get(pk=relation_draft.pk)
        rel_approved = rel_draft.approved

        # assert rel_approved is not None
        assert rel_draft.relation_name == rel_approved.relation_name == 'relation one v3'
        assert rel_draft.relation_title == rel_approved.relation_title == 'relation title now set'

        assert logs_output == [
            "WARNING:bx_django_utils.approve_workflow.models:Not ready to approve:"
            " pk:UUID('00000000-0000-0000-0000-000000000001') model:ApproveTestModel",

            'INFO:bx_django_utils.approve_workflow.models:<RelatedApproveTestModel '
            'pk:00000000-0000-0000-0000-000000000002 (draft)> was approved to '
            f'<RelatedApproveTestModel pk:{rel_approved.pk} (approved)>',

            'INFO:bx_django_utils.approve_workflow.models:<ApproveTestModel '
            'pk:00000000-0000-0000-0000-000000000001 (draft, not ready)> was approved to '
            f'<ApproveTestModel pk:{approved.pk} (approved)>',
        ]

        messages = [m.message for m in get_messages(response.wsgi_request)]

        # "normalize" different Django versions:
        messages = [m.replace('“', '"').replace('”', '"') for m in messages]

        assert messages == [
            'The approve test model "<a href="/admin/approve_workflow_test_app/approvetestmodel'
            '/00000000-0000-0000-0000-000000000001/change/">&lt;ApproveTestModel '
            'pk:00000000-0000-0000-0000-000000000001 (draft, not ready)&gt;</a>" was '
            'changed successfully.',

            'Warning: "Ready to Approve" flag was not set!',

            f'<ApproveTestModel pk:{approved.pk} (approved)> was approved'
        ]
