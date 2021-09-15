from unittest import mock

import django
from bx_py_utils.test_utils.datetime import parse_dt
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from bx_django_utils.models.manipulate import create, create_or_update
from bx_django_utils.test_utils.datetime import MockDatetimeGenerator
from bx_django_utils.test_utils.model_clean_assert import AssertModelCleanCalled
from bx_django_utils_tests.test_app.models import CreateOrUpdateTestModel


class ModelManipulateTestCase(TestCase):
    @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
    def test_create_or_update(self):

        # create a new entry:

        with AssertModelCleanCalled() as cm:
            instance, created, updated_fields = create_or_update(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='First entry',
                slug='first'
            )
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.name == 'First entry'
            assert instance.slug == 'first'
            assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
            assert instance.update_dt == parse_dt('2001-01-01T00:00:00+0000')
            assert created is True
            assert updated_fields is None
        cm.assert_no_missing_cleans()

        # Change only 'slug'

        with AssertModelCleanCalled() as cm:
            instance, created, updated_fields = create_or_update(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='First entry',
                slug='change-value'
            )
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.name == 'First entry'
            assert instance.slug == 'change-value'
            assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')  # not changed!
            assert instance.update_dt == parse_dt('2002-01-01T00:00:00+0000')
            assert created is False
            assert updated_fields == ['slug']
        cm.assert_no_missing_cleans()

        # Change 'name' and 'slug':

        with AssertModelCleanCalled() as cm:
            instance, created, updated_fields = create_or_update(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='New name !',
                slug='new-slug'
            )
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.name == 'New name !'
            assert instance.slug == 'new-slug'
            assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')  # not changed!
            assert instance.update_dt == parse_dt('2003-01-01T00:00:00+0000')
            assert created is False
            assert updated_fields == ['name', 'slug']
        cm.assert_no_missing_cleans()

        # Nothing changed:

        instance, created, updated_fields = create_or_update(
            ModelClass=CreateOrUpdateTestModel,
            lookup={'id': 1},
            name='New name !',
            slug='new-slug'
        )
        assert isinstance(instance, CreateOrUpdateTestModel)
        assert instance.id == 1
        assert instance.name == 'New name !'
        assert instance.slug == 'new-slug'
        assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
        assert instance.update_dt == parse_dt('2003-01-01T00:00:00+0000')  # not changed!
        assert created is False
        assert updated_fields == []

    def test_non_valid(self):
        msg = str(validate_slug.message)
        with self.assertRaisesMessage(ValidationError, msg):
            create_or_update(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='foo',
                slug='this is no Slug !'
            )

        # Update existing entry with non-valid values should also not work:

        CreateOrUpdateTestModel(id=1, name='foo', slug='bar')
        with self.assertRaisesMessage(ValidationError, msg):
            create_or_update(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='foo',
                slug='this is no Slug !'
            )

    def test_disable_full_clean(self):
        # Create a new entry without "full_clean()" call:
        with AssertModelCleanCalled() as cm:
            instance, created, updated_fields = create_or_update(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                call_full_clean=False,
                slug='This is not a valid slug!'
            )
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.slug == 'This is not a valid slug!'
            assert created is True
            assert updated_fields is None
        assert cm.called_cleans == []
        assert len(cm.missing_cleans) == 1

        # Change existing without "full_clean()" call:
        with AssertModelCleanCalled() as cm:
            instance, created, updated_fields = create_or_update(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                call_full_clean=False,
                slug='Also no valid slug!'
            )
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.slug == 'Also no valid slug!'
            assert created is False
            assert updated_fields == ['slug']
        assert cm.called_cleans == []
        assert len(cm.missing_cleans) == 1

    @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
    def test_create_or_update_without_lookup(self):
        # create a new entry:

        with AssertModelCleanCalled() as cm:
            instance, created, updated_fields = create_or_update(
                ModelClass=CreateOrUpdateTestModel,
                lookup=None,
                name='First entry',
                slug='first'
            )
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.pk is not None
            assert instance.name == 'First entry'
            assert instance.slug == 'first'
            assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
            assert instance.update_dt == parse_dt('2001-01-01T00:00:00+0000')
            assert created is True
            assert updated_fields is None
        cm.assert_no_missing_cleans()

    @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
    def test_create(self):
        # create a new entry:

        with AssertModelCleanCalled() as cm:
            instance = create(
                ModelClass=CreateOrUpdateTestModel,
                name='First entry',
                slug='first'
            )
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.pk is not None
            assert instance.name == 'First entry'
            assert instance.slug == 'first'
            assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
            assert instance.update_dt == parse_dt('2001-01-01T00:00:00+0000')
        cm.assert_no_missing_cleans()

        # Cannot create an already existing model
        with self.assertRaises(IntegrityError):
            create(
                ModelClass=CreateOrUpdateTestModel,
                id=instance.id,
                name='second create',
                slug='second'
            )
