from unittest import mock

from django.test import TestCase
from django.utils import timezone

from bx_py_utils.models.manipulate import create_or_update
from bx_py_utils_tests.test_app.models import CreateOrUpdateTestModel
from bx_py_utils_tests.tests.utils import MockDatetimeGenerator, parse_dt


class ModelManipulateTestCase(TestCase):
    @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
    def test_create_or_update(self):

        # create a new entry:

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

        # Change only 'slug'

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

        # Change 'name' and 'slug':

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
