from unittest import mock

from bx_py_utils.test_utils.mock_uuid import MockUUIDGenerator
from django.test import TestCase

from bx_django_utils.test_utils.users import assert_user_properties, filter_permission_names, make_test_user


class UserUtilsTestCase(TestCase):
    def test_assert_user_properties_wrong_user_object(self):
        class Wrong:
            pass

        with self.assertRaisesMessage(
            AssertionError, "Given user object (type='Wrong') is not a 'auth.User' instance."
        ):
            assert_user_properties(user=Wrong(), properties={})

    def test_make_test_user1(self):
        with mock.patch('uuid.uuid4', MockUUIDGenerator()):
            user = make_test_user()

        # we can check only a few properties:
        assert_user_properties(
            user, properties={'username': 'test 89e6b14d-622a-409f-88de-000000000001'}
        )
        assert_user_properties(user, properties={'email': 'test@test.tld', 'permissions': []})

        # Check everything:
        assert_user_properties(
            user,
            properties={
                'username': 'test 89e6b14d-622a-409f-88de-000000000001',
                'email': 'test@test.tld',
                'is_active': True,
                'is_staff': True,
                'is_superuser': False,
                'permissions': [],
            },
            raw_password='t',
        )

    def test_make_test_user_permissions(self):
        user = make_test_user(
            permissions=filter_permission_names(['auth.add_user', 'auth.change_user']),
        )
        assert_user_properties(
            user,
            properties={
                'permissions': ['auth.add_user', 'auth.change_user'],
            },
        )

    def test_make_test_user_flags(self):
        assert_user_properties(
            user=make_test_user(is_active=False),
            properties={'is_active': False},
        )
        assert_user_properties(
            user=make_test_user(is_staff=False),
            properties={'is_staff': False},
        )
        assert_user_properties(
            user=make_test_user(is_superuser=True),
            properties={'is_superuser': True},
        )
