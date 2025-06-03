from uuid import UUID

from django.contrib.auth.models import User
from django.test import TestCase
from model_bakery import baker

from bx_django_utils.test_utils.model_primary_key import deterministic_primary_key
from bx_django_utils_tests.approve_workflow_test_app.models import ApproveTestModel


class TestUtilsTestCase(TestCase):
    def test_deterministic_primary_key_integer_pk(self):
        """DocWrite: test-tools.md ## deterministic_primary_key()
        With this context manager can be used to enforce a deterministic primary key for a model
        in deeper code paths.
        It used the `post_init` signal to set a deterministic primary key,
        before the model will be stored into the database.
        e.g.:
            with deterministic_primary_key(MyModel1, MyModel2):
                MyModel.objects.create()
                baker.make(MyModel2)

        Models with integer primary key will get 10000 + counter + 1
        Looks like:
        * `10001`
        * `10002`
        """
        with deterministic_primary_key(User):
            user1 = baker.make(User, username='baker')
            self.assertEqual(user1.pk, 10001)
            user2 = User.objects.create(username='create')
            self.assertEqual(user2.pk, 10002)

            self.assertEqual(
                sorted(User.objects.values_list('id', 'username')),
                [(10001, 'baker'), (10002, 'create')],
            )

            # Handle existing primary key -> Don't increment, so that a new object will be created!
            user = User(username='NEW NAME', id=10001)
            user.save()

            self.assertEqual(
                sorted(User.objects.values_list('id', 'username')),
                [(10001, 'NEW NAME'), (10002, 'create')],
            )

    def test_deterministic_primary_key_one_uuid_model(self):
        """DocWrite: test-tools.md ## deterministic_primary_key()
        Models with UUID primary key will get a UUID with a
        prefix based on the model name and a counter. Looks like:
        * `UUID('bf264d42-0000-0000-0000-000000000001')`
        * `UUID('bf264d42-0000-0000-0000-000000000002')`
        """
        with deterministic_primary_key(ApproveTestModel):
            obj1 = baker.make(ApproveTestModel, name='baker')
            self.assertEqual(obj1.pk, UUID('bf264d42-0000-0000-0000-000000000001'))
            obj2 = ApproveTestModel.objects.create(name='create')
            self.assertEqual(obj2.pk, UUID('bf264d42-0000-0000-0000-000000000002'))

        self.assertEqual(
            sorted(ApproveTestModel.objects.values_list('id', 'name')),
            [
                (UUID('bf264d42-0000-0000-0000-000000000001'), 'baker'),
                (UUID('bf264d42-0000-0000-0000-000000000002'), 'create'),
            ],
        )

    def test_deterministic_primary_key_force(self):
        """DocWrite: test-tools.md ## deterministic_primary_key()
        There is the optional keyword argument `force_overwrite_pk`,
        which forces overwrite a existing primary key.
        """
        with deterministic_primary_key(User, force_overwrite_pk=True):
            user1 = baker.make(User, id=123)
            self.assertEqual(user1.pk, 10001)  # 123 overwritten

        """DocWrite: test-tools.md ## deterministic_primary_key()
        `force_overwrite_pk` is enabled by default."""
        with deterministic_primary_key(User):
            user2 = baker.make(User, id=123)
            self.assertEqual(user2.pk, 10002)  # 123 overwritten

        with deterministic_primary_key(User, force_overwrite_pk=False):
            user3 = baker.make(User, id=123)
            self.assertEqual(user3.pk, 123)  # 123 not overwritten

    def test_deterministic_primary_key_two_models(self):
        with deterministic_primary_key(ApproveTestModel, User):
            baker.make(ApproveTestModel, id=None, name='baker')
            ApproveTestModel.objects.create(name='create')
            baker.make(User, username='baker')
            User.objects.create(username='create')

        self.assertEqual(
            sorted(User.objects.values_list('id', 'username')),
            [(10001, 'baker'), (10002, 'create')],
        )
        self.assertEqual(
            sorted(ApproveTestModel.objects.values_list('id', 'name')),
            [
                (UUID('bf264d42-0000-0000-0000-000000000001'), 'baker'),
                (UUID('bf264d42-0000-0000-0000-000000000002'), 'create'),
            ],
        )
