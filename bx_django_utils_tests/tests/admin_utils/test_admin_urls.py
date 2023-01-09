from django.contrib.auth.models import User
from django.test import TestCase
from model_bakery import baker

from bx_django_utils.admin_utils.admin_urls import (
    admin_change_url,
    admin_changelist_url,
    admin_delete_url,
    admin_history_url,
    admin_model_url,
)


class AdminUrlsSimpleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = baker.make(User, id=1)

    def test_admin_model_url(self):
        # defaults to "change":
        self.assertEqual(admin_model_url(model_or_instance=self.user), '/admin/auth/user/1/change/')

        # defaults to "changelist":
        self.assertEqual(admin_model_url(model_or_instance=User), '/admin/auth/user/')

        # All action variants for a instance:
        self.assertEqual(
            admin_model_url(model_or_instance=self.user, action='change'),
            '/admin/auth/user/1/change/',
        )
        self.assertEqual(
            admin_model_url(model_or_instance=self.user, action='history'),
            '/admin/auth/user/1/history/',
        )
        self.assertEqual(
            admin_model_url(model_or_instance=self.user, action='delete'),
            '/admin/auth/user/1/delete/',
        )

        # All action variants for a model class:
        self.assertEqual(
            admin_model_url(model_or_instance=User, action='changelist'), '/admin/auth/user/'
        )
        self.assertEqual(
            admin_model_url(model_or_instance=User, action='add'), '/admin/auth/user/add/'
        )

        # Optional parameters:
        url = admin_model_url(model_or_instance=User, params=dict(is_staff__exact=1))
        self.assertEqual(url, '/admin/auth/user/?is_staff__exact=1')

        with self.assertRaisesMessage(
            AssertionError, "Action: 'Bam!' is not one of changelist, add, history, delete, change"
        ):
            admin_model_url(model_or_instance=User, action='Bam!')

        with self.assertRaisesMessage(AssertionError, 'is no model instance'):
            admin_model_url(model_or_instance=User, action='change')

    def test_admin_change_url(self):
        self.assertEqual(admin_change_url(self.user), '/admin/auth/user/1/change/')

    def test_admin_history_url(self):
        self.assertEqual(admin_history_url(self.user), '/admin/auth/user/1/history/')

    def test_admin_delete_url(self):
        self.assertEqual(admin_delete_url(self.user), '/admin/auth/user/1/delete/')

    def test_admin_changelist_url(self):
        self.assertEqual(admin_changelist_url(self.user), '/admin/auth/user/')
        self.assertEqual(admin_changelist_url(User), '/admin/auth/user/')
