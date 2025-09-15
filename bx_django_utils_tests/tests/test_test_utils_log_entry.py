from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.models import User
from django.test import TestCase
from model_bakery import baker

from bx_django_utils.admin_utils.log_entry import create_log_entry
from bx_django_utils.test_utils.log_entry import get_django_log_entries


class LogEntryTestCase(TestCase):
    def test_get_django_log_entries(self):
        self.assertEqual(get_django_log_entries(), [])

        user = baker.make(User, pk=1, username='foo')
        create_log_entry(user=user, instance=user, action_flag=ADDITION, change_message='Add User')
        self.assertEqual(
            get_django_log_entries(),
            [('user', 'foo', 1, 'Add User')],
        )

        create_log_entry(user=user, instance=user, action_flag=CHANGE, change_message='Change User')
        self.assertEqual(
            get_django_log_entries(clear=True),
            [
                ('user', 'foo', 1, 'Add User'),
                ('user', 'foo', 2, 'Change User'),
            ],
        )

        create_log_entry(user=user, instance=user, action_flag=DELETION, change_message='Delete User')
        self.assertEqual(
            get_django_log_entries(fields=('action_flag', 'change_message')),
            [(3, 'Delete User')],
        )
