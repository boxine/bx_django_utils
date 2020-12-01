from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from bx_py_utils.models.manipulate import create_or_update
from bx_py_utils.test_utils.datetime import MockDatetimeGenerator, parse_dt
from bx_py_utils.test_utils.model_clean_assert import AssertModelCleanCalled
from bx_py_utils_tests.test_app.models import CreateOrUpdateTestModel


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
        msg = (
            "{'slug': ['Enter a valid “slug” consisting of letters,"
            " numbers, underscores or hyphens.']}"
        )
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
