from unittest import mock
from uuid import UUID

from bx_py_utils.test_utils.datetime import parse_dt
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from bx_django_utils.models.manipulate import (
    STORE_BEHAVIOR_IGNORE,
    STORE_BEHAVIOR_SET_IF_EMPTY,
    STORE_BEHAVIOR_SKIP_EMPTY,
    CreateOrUpdateResult,
    FieldUpdate,
    InvalidStoreBehavior,
    create,
    create_or_update,
    create_or_update2,
)
from bx_django_utils.test_utils.datetime import MockDatetimeGenerator
from bx_django_utils.test_utils.model_clean_assert import AssertModelCleanCalled
from bx_django_utils_tests.test_app.models import (
    CreateOrUpdateTestModel,
    StoreSaveModel,
    TimetrackingTestModel,
    PolymorphicCar,
    PolymorphicBike,
)


class ModelManipulateTestCase(TestCase):
    def test_deprecated_create_or_update(self):
        with self.assertWarns(DeprecationWarning):
            instance, created, updated_fields = create_or_update(
                ModelClass=CreateOrUpdateTestModel, name='foo', slug='bar'
            )
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.name == 'foo'
            assert created is True
            assert updated_fields is None  # None and not []

    @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
    def test_create_or_update2(self):

        # create a new entry:

        with AssertModelCleanCalled() as cm:
            result = create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='First entry',
                slug='first'
            )
            self.assertIsInstance(result, CreateOrUpdateResult)
            instance = result.instance
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.name == 'First entry'
            assert instance.slug == 'first'
            assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
            assert instance.update_dt == parse_dt('2001-01-01T00:00:00+0000')
            assert result.created is True
            assert result.ignored_fields == []
            assert result.not_overwritten_fields == []
            # Not set if new instance created:
            self.assertEqual(result.updated_fields, [])
            self.assertEqual(result.update_info, [])
        cm.assert_no_missing_cleans()

        # Change only 'slug'

        with AssertModelCleanCalled() as cm:
            result = create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='First entry',
                slug='change-value'
            )
            instance = result.instance
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.name == 'First entry'
            assert instance.slug == 'change-value'
            assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')  # not changed!
            assert instance.update_dt == parse_dt('2002-01-01T00:00:00+0000')
            assert result.created is False
            assert result.ignored_fields == []
            assert result.not_overwritten_fields == []
            self.assertEqual(result.updated_fields, ['slug'])
            self.assertEqual(
                result.update_info, [FieldUpdate(field_name='slug', old_value='first', new_value='change-value')]
            )
        cm.assert_no_missing_cleans()

        # Change 'name' and 'slug':

        with AssertModelCleanCalled() as cm:
            result = create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='New name !',
                slug='new-slug'
            )
            instance = result.instance
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.name == 'New name !'
            assert instance.slug == 'new-slug'
            assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')  # not changed!
            assert instance.update_dt == parse_dt('2003-01-01T00:00:00+0000')
            assert result.created is False
            assert result.ignored_fields == []
            assert result.not_overwritten_fields == []
            self.assertEqual(result.updated_fields, ['name', 'slug'])
            self.assertEqual(
                result.update_info,
                [
                    FieldUpdate(field_name='name', old_value='First entry', new_value='New name !'),
                    FieldUpdate(field_name='slug', old_value='change-value', new_value='new-slug'),
                ],
            )
        cm.assert_no_missing_cleans()

        # Nothing changed:

        result = create_or_update2(
            ModelClass=CreateOrUpdateTestModel,
            lookup={'id': 1},
            name='New name !',
            slug='new-slug'
        )
        instance = result.instance
        assert isinstance(instance, CreateOrUpdateTestModel)
        assert instance.id == 1
        assert instance.name == 'New name !'
        assert instance.slug == 'new-slug'
        assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
        assert instance.update_dt == parse_dt('2003-01-01T00:00:00+0000')  # not changed!
        assert result.created is False
        assert result.ignored_fields == []
        assert result.not_overwritten_fields == []
        self.assertEqual(result.updated_fields, [])
        self.assertEqual(result.update_info, [])

    def test_non_valid(self):
        msg = str(validate_slug.message)
        with self.assertRaisesMessage(ValidationError, msg):
            create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='foo',
                slug='this is no Slug !'
            )

        # Update existing entry with non-valid values should also not work:

        CreateOrUpdateTestModel(id=1, name='foo', slug='bar')
        with self.assertRaisesMessage(ValidationError, msg):
            create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                name='foo',
                slug='this is no Slug !'
            )

    def test_disable_full_clean(self):
        # Create a new entry without "full_clean()" call:
        with AssertModelCleanCalled() as cm:
            result = create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                call_full_clean=False,
                slug='This is not a valid slug!'
            )
            instance = result.instance
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.slug == 'This is not a valid slug!'
            assert result.created is True
            assert result.updated_fields == []
        assert cm.called_cleans == []
        assert len(cm.missing_cleans) == 1

        # Change existing without "full_clean()" call:
        with AssertModelCleanCalled() as cm:
            result = create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                call_full_clean=False,
                slug='Also no valid slug!'
            )
            instance = result.instance
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.id == 1
            assert instance.slug == 'Also no valid slug!'
            assert result.created is False
            assert result.updated_fields == ['slug']
        assert cm.called_cleans == []
        assert len(cm.missing_cleans) == 1

    @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
    def test_create_or_update_without_lookup(self):
        # create a new entry:

        with AssertModelCleanCalled() as cm:
            result = create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                lookup=None,
                name='First entry',
                slug='first'
            )
            instance = result.instance
            assert isinstance(instance, CreateOrUpdateTestModel)
            assert instance.pk is not None
            assert instance.name == 'First entry'
            assert instance.slug == 'first'
            assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
            assert instance.update_dt == parse_dt('2001-01-01T00:00:00+0000')
            assert result.created is True
            assert result.updated_fields == []
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

    @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
    def test_store_behavior(self):
        test_relation1 = TimetrackingTestModel(
            create_dt=parse_dt('2002-02-02T00:00:00+0000'),
            update_dt=parse_dt('2003-03-03T00:00:00+0000')
        )
        test_relation1.save(update_dt=False)

        test_relation2 = TimetrackingTestModel(
            create_dt=parse_dt('2004-04-04T00:00:00+0000'),
            update_dt=parse_dt('2005-05-05T00:00:00+0000')
        )
        test_relation2.save(update_dt=False)

        # Create object and respect "store_behavior"

        result = create_or_update2(
            ModelClass=CreateOrUpdateTestModel,
            lookup=None,  # force create object!
            store_behavior={
                # 'name' is missing here -> normal behavior: overwrite existing values
                'slug': STORE_BEHAVIOR_SET_IF_EMPTY,
                'many2one_rel': STORE_BEHAVIOR_SET_IF_EMPTY,
                'blank_field': STORE_BEHAVIOR_IGNORE,
                'null_field': STORE_BEHAVIOR_IGNORE,
            },
            name='name1',
            slug='slug1',
            many2one_rel=test_relation1,
            blank_field='ignored',
            null_field='ignored',
        )
        assert result.created is True
        assert result.updated_fields == []  # Object created!
        assert sorted(result.ignored_fields) == ['blank_field', 'null_field']
        assert result.not_overwritten_fields == []
        assert result.skip_empty_values == []
        instance = result.instance
        assert instance.name == 'name1'
        assert instance.slug == 'slug1'
        assert instance.many2one_rel.create_dt == parse_dt('2002-02-02T00:00:00+0000')
        assert instance.many2one_rel.update_dt == parse_dt('2003-03-03T00:00:00+0000')
        assert instance.blank_field == ''
        assert instance.null_field is None
        assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
        assert instance.update_dt == parse_dt('2001-01-01T00:00:00+0000')

        # Update existing instance

        result = create_or_update2(
            ModelClass=CreateOrUpdateTestModel,
            lookup={'pk': instance.pk},
            store_behavior={
                # 'name' is missing here -> normal behavior: overwrite existing values
                'slug': STORE_BEHAVIOR_SET_IF_EMPTY,
                'many2one_rel': STORE_BEHAVIOR_SKIP_EMPTY,  # given relation is not empty
                'blank_field': STORE_BEHAVIOR_SET_IF_EMPTY,
                'null_field': STORE_BEHAVIOR_SET_IF_EMPTY,
            },
            name='name2',
            slug='not-overwritten',
            many2one_rel=test_relation2,
            blank_field='set blank field 1',
            null_field='set null field 1',
        )
        instance = result.instance
        assert result.created is False
        assert instance.name == 'name2'
        assert instance.slug == 'slug1'
        assert instance.many2one_rel.create_dt == parse_dt('2004-04-04T00:00:00+0000')  # updated
        assert instance.many2one_rel.update_dt == parse_dt('2005-05-05T00:00:00+0000')  # updated
        assert instance.blank_field == 'set blank field 1'
        assert instance.null_field == 'set null field 1'
        assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
        assert instance.update_dt == parse_dt('2002-01-01T00:00:00+0000')
        assert sorted(result.updated_fields) == [
            'blank_field', 'many2one_rel', 'name', 'null_field'
        ]
        assert result.ignored_fields == []
        assert result.not_overwritten_fields == ['slug']
        assert result.skip_empty_values == []

        # Skip empty values

        result = create_or_update2(
            ModelClass=CreateOrUpdateTestModel,
            lookup={'pk': instance.pk},
            store_behavior={
                'slug': STORE_BEHAVIOR_IGNORE,
                'many2one_rel': STORE_BEHAVIOR_SKIP_EMPTY,
                'blank_field': STORE_BEHAVIOR_SKIP_EMPTY,
                'null_field': STORE_BEHAVIOR_SKIP_EMPTY,
            },
            name='name3',
            slug='will-be-ignored',
            many2one_rel=None,
            blank_field='',  # a empty value
            null_field=None,  # a empty value
        )
        instance = result.instance
        assert result.created is False
        assert instance.name == 'name3'  # new name
        assert instance.slug == 'slug1'  # unchanged
        assert instance.many2one_rel.create_dt == parse_dt('2004-04-04T00:00:00+0000')  # unchanged
        assert instance.many2one_rel.update_dt == parse_dt('2005-05-05T00:00:00+0000')  # unchanged
        assert instance.blank_field == 'set blank field 1'  # unchanged
        assert instance.null_field == 'set null field 1'  # unchanged
        assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
        assert instance.update_dt == parse_dt('2003-01-01T00:00:00+0000')
        assert result.updated_fields == ['name']
        assert result.ignored_fields == ['slug']
        assert result.not_overwritten_fields == []
        assert sorted(result.skip_empty_values) == [
            'blank_field', 'many2one_rel', 'null_field'
        ]

        # Store empty values

        result = create_or_update2(
            ModelClass=CreateOrUpdateTestModel,
            lookup={'pk': instance.pk},
            store_behavior={
                'name': STORE_BEHAVIOR_IGNORE,
                'slug': STORE_BEHAVIOR_IGNORE,
            },
            name='Not Overwritten !',
            # "slug" missing here, but can be set in "store_behavior"
            many2one_rel=None,  # can be set to "empty"
            blank_field='',  # can be set to "empty"
            null_field=None,  # can be set to "empty"
        )
        instance = result.instance
        assert result.created is False
        assert instance.name == 'name3'  # unchanged
        assert instance.slug == 'slug1'  # unchanged
        assert instance.many2one_rel is None
        assert instance.blank_field == ''
        assert instance.null_field is None
        assert instance.create_dt == parse_dt('2001-01-01T00:00:00+0000')
        assert instance.update_dt == parse_dt('2004-01-01T00:00:00+0000')
        assert sorted(result.updated_fields) == ['blank_field', 'many2one_rel', 'null_field']
        assert result.ignored_fields == ['name']
        assert result.not_overwritten_fields == []

        # We accept only existing field names in store_behavior:

        err_msg = (
            "store_behavior field name 'wrong' is not one of:"
            " ['blank_field', 'create_dt', 'id', 'many2one_rel',"
            " 'name', 'null_field', 'slug', 'update_dt', 'uuid_field']"
        )
        with self.assertRaisesMessage(InvalidStoreBehavior, err_msg):
            create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                store_behavior={
                    'name': STORE_BEHAVIOR_IGNORE,
                    'slug': STORE_BEHAVIOR_SET_IF_EMPTY,
                    # We check the field names:
                    'wrong': STORE_BEHAVIOR_IGNORE,
                },
            )

        assert CreateOrUpdateTestModel.objects.count() == 1

    @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
    def test_save_kwargs(self):
        obj = create_or_update2(
            ModelClass=StoreSaveModel,
            name='foobar',
            save_kwargs={'arg': 'original'},
        ).instance
        assert obj.name == 'foobar'

        create_or_update2(
            ModelClass=StoreSaveModel,
            lookup={'pk': obj.pk},
            name='bazqux',
            save_kwargs={'other_arg': 'changed'},
        )
        obj.refresh_from_db()
        assert obj.name == 'bazqux'

        create_or_update2(
            ModelClass=StoreSaveModel,
            lookup={'pk': obj.pk},
            name='final',
            save_kwargs={},
        )
        obj.refresh_from_db()
        assert obj.name == 'final'

        assert obj._save_calls.saves == [
            {'arg': 'original'},
            {'other_arg': 'changed'},
            {},
        ]

    def test_create_or_update2_uuid(self):
        baker.make(
            CreateOrUpdateTestModel, id=1, uuid_field='00000000-0000-0000-0000-000000000001', name='foo', slug='foo'
        )

        # Change UUID field by string:

        result: CreateOrUpdateResult = create_or_update2(
            ModelClass=CreateOrUpdateTestModel,
            lookup={'id': 1},
            uuid_field='00000000-0000-0000-0000-000000000002',
        )
        self.assertIs(result.created, False)
        self.assertEqual(result.updated_fields, ['uuid_field'])

        # Change UUID field by object:

        result: CreateOrUpdateResult = create_or_update2(
            ModelClass=CreateOrUpdateTestModel,
            lookup={'id': 1},
            uuid_field=UUID('00000000-0000-0000-0000-000000000003'),
        )
        self.assertIs(result.created, False)
        self.assertEqual(result.updated_fields, ['uuid_field'])

        # Don't change anything, use UUID as string:

        result: CreateOrUpdateResult = create_or_update2(
            ModelClass=CreateOrUpdateTestModel,
            lookup={'id': 1},
            uuid_field='00000000-0000-0000-0000-000000000003',
        )
        self.assertIs(result.created, False)
        self.assertEqual(result.updated_fields, [])

        # Don't change anything, use UUID object:

        result: CreateOrUpdateResult = create_or_update2(
            ModelClass=CreateOrUpdateTestModel,
            lookup={'id': 1},
            uuid_field=UUID('00000000-0000-0000-0000-000000000003'),
        )
        self.assertIs(result.created, False)
        self.assertEqual(result.updated_fields, [])

        # Feed a non UUID will raise a normal error:

        with self.assertRaisesMessage(ValidationError, 'is not a valid UUID'):
            create_or_update2(
                ModelClass=CreateOrUpdateTestModel,
                lookup={'id': 1},
                uuid_field='Bam !',
            )

    def test_polymorphic_change(self):
        pk = 'D-TO123'
        car = PolymorphicCar.objects.create(license_plate=pk, color='red')

        with self.assertRaisesMessage(ValidationError, 'Polymorphic vehicle with this License plate already exists.'):
            create_or_update2(
                ModelClass=PolymorphicBike,
                lookup={'license_plate': pk},
                validate_unique=True,
                color='blue',
            )

        # This should not crash
        car.refresh_from_db()
