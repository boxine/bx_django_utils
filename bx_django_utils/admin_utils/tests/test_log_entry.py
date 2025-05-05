from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.test import TestCase
from model_bakery import baker

from bx_django_utils.admin_utils.log_entry import (
    create_log_entry,
    get_change_message_strings,
    get_log_entry_qs,
    get_log_message_data,
)
from bx_django_utils.test_utils.assert_queries import AssertQueries


class LogEntryTestCase(TestCase):
    """"""  # noqa - don't add in README

    maxDiff = None

    def test_basic(self):
        user1 = baker.make(User, pk=1, username='foo')
        user2 = baker.make(User, pk=2, username='bar')

        # Test create_log_entry():
        # Create some log entries with "change_message" values like in the Django admin:
        create_log_entry(user=user1, instance=user2, action_flag=ADDITION, change_message='[{"added": {}}]')
        create_log_entry(
            user=user1,
            instance=user2,
            action_flag=CHANGE,
            change_message='[{"changed": {"fields": ["Staff status"]}}]',
        )
        create_log_entry(
            user=user1,
            instance=user2,
            action_flag=DELETION,
            # WTF: The DELETION "change_message" in Django admin is empty.
            # But the dLogEntry.get_change_message() used this data scheme:
            change_message='[{"deleted": {"name": "faked name", "object": "faked object"}}]',
        )

        # Add a "own" log entry with unstructured "change_message" value:
        with AssertQueries(query_explain=False) as queries:
            create_log_entry(
                user=user1,
                instance=user2,
                action_flag=CHANGE,
                change_message='This is a test message.',
            )
        queries.assert_queries(table_counts={'auth_user': 1, 'django_admin_log': 1, 'django_content_type': 1})

        # Check get_log_entry_qs():
        qs = get_log_entry_qs()
        self.assertIsInstance(qs, QuerySet)
        self.assertEqual(qs.count(), LogEntry.objects.all().count())
        self.assertEqual(
            list(qs.values('user_id', 'object_id', 'object_repr', 'action_flag', 'change_message')),
            [
                {
                    'user_id': 1,
                    'object_id': '2',
                    'object_repr': 'bar',
                    'action_flag': 1,
                    'change_message': '[{"added": {}}]',
                },
                {
                    'user_id': 1,
                    'object_id': '2',
                    'object_repr': 'bar',
                    'action_flag': 2,
                    'change_message': '[{"changed": {"fields": ["Staff status"]}}]',
                },
                {
                    'user_id': 1,
                    'object_id': '2',
                    'object_repr': 'bar',
                    'action_flag': 3,
                    'change_message': '[{"deleted": {"name": "faked name", "object": "faked object"}}]',
                },
                {
                    'user_id': 1,
                    'object_id': '2',
                    'object_repr': 'bar',
                    'action_flag': 2,
                    'change_message': 'This is a test message.',
                },
            ],
        )
        self.assertEqual(
            list(get_log_entry_qs(model=User, object_id='2', action_flag=ADDITION).values('change_message')),
            [{'change_message': '[{"added": {}}]'}],
        )

        # Test get_change_message_strings():
        with AssertQueries(query_explain=False) as queries:
            message_strings = get_change_message_strings()
        self.assertEqual(
            message_strings,
            ['Added.', 'Changed Staff status.', 'Deleted faked name “faked object”.', 'This is a test message.'],
        )
        queries.assert_queries(table_counts={'django_admin_log': 1})

        # Test get_log_message_data():
        with AssertQueries(query_explain=False) as queries:
            message_data = get_log_message_data()
        self.assertEqual(
            message_data,
            [
                {'added': {}},
                {'changed': {'fields': ['Staff status']}},
                {'deleted': {'name': 'faked name', 'object': 'faked object'}},
                'Changed “bar” — This is a test message.',
            ],
        )
        queries.assert_queries(table_counts={'django_admin_log': 1})

        # create_log_entry() validates the created entry:
        with self.assertRaisesMessage(
            ValueError,
            expected_message="Field 'action_flag' expected a number but got 'Bam!'.",
        ):
            create_log_entry(
                user=user1,
                instance=user2,
                action_flag='Bam!',
                change_message='foo',
            )
