import json
import re
from itertools import product

from bx_py_utils.test_utils.snapshot import assert_html_snapshot
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import translation

from bx_django_utils.models.manipulate import FieldUpdate, create_or_update2
from bx_django_utils.test_utils.users import make_test_user
from bx_django_utils.translation import (
    FieldTranslation,
    TranslationField,
    TranslationFormField,
    TranslationSlugField,
    TranslationWidget,
    create_or_update_translation_callback,
    slug_generator,
)
from bx_django_utils_tests.test_app.models import RawTranslatedModel, TranslatedModel, TranslatedSlugTestModel


class TranslationFieldTestCase(TestCase):
    def test_stores_only_wanted_languages(self):
        obj = TranslatedModel(
            translated={'de-de': 'Hallo', 'en-us': 'Hello', 'es': 'Hola', 'it': 'Ciao'},
            translated_multiline={'de-de': 'Hallo'},
        )
        with self.assertRaisesMessage(ValidationError, 'Unknown translation language(s): it'):
            obj.full_clean()

        obj = TranslatedModel(
            translated={'de-de': 'Hallo'},
            translated_multiline={'de-de': 'Hallo', 'en-us': 'Hello', 'es': 'Hola', 'it-it': 'Ciao', 'xx': 'foo'},
        )
        with self.assertRaisesMessage(ValidationError, 'Unknown translation language(s): it-it, xx'):
            obj.full_clean()

    def test_field_translation(self):
        translated = FieldTranslation()
        self.assertEqual(translated.get_first([1, 2, 3]), FieldTranslation.UNTRANSLATED)
        self.assertEqual(repr(translated), 'FieldTranslation({})')

        translated = FieldTranslation({'de-de': 'Hallo'})
        self.assertEqual(repr(translated), "FieldTranslation({'de-de': 'Hallo'})")
        self.assertEqual(translated.get_first(['foo', 'bar', 'en-gb', 'de-de']), 'Hallo')

        obj1 = TranslatedModel.objects.create(translated={'de-de': 'Hallo 1', 'en-us': 'Hello 1'})
        obj1.full_clean()
        self.assertEqual(repr(obj1.translated), "FieldTranslation({'de-de': 'Hallo 1', 'en-us': 'Hello 1'})")

        obj2 = TranslatedModel.objects.create(translated={'de-de': 'Hallo 2', 'en-us': 'Hello 2'})
        obj2.full_clean()

        self.assertNotEqual(obj1.translated, obj2.translated)

        qs = TranslatedModel.objects.order_by('translated').values('translated')
        self.assertQuerysetEqual(
            qs,
            [
                {'translated': FieldTranslation({'de-de': 'Hallo 1', 'en-us': 'Hello 1'})},
                {'translated': FieldTranslation({'de-de': 'Hallo 2', 'en-us': 'Hello 2'})},
            ],
        )

    def test_blank(self):
        obj = TranslatedModel()
        with self.assertRaisesMessage(ValidationError, 'At least one translation is required.'):
            obj.full_clean()

        obj.translated = {}
        with self.assertRaisesMessage(ValidationError, 'At least one translation is required.'):
            obj.full_clean()

        obj.translated = {'de-de': ''}
        with self.assertRaisesMessage(ValidationError, 'At least one translation is required.'):
            obj.full_clean()

        obj.translated = {'de-de': 'a value'}
        obj.full_clean()

    def test_empty_translations_from_db(self):
        # Store empty values using the RawTranslatedModel:
        RawTranslatedModel.objects.create(translated={'de-de': 'A value', 'en-gb': '', 'en-us': None})
        raw_obj = RawTranslatedModel.objects.first()
        self.assertEqual(raw_obj.translated, {'de-de': 'A value', 'en-gb': '', 'en-us': None})

        # Empty values from DB will be ignored:
        obj = TranslatedModel.objects.first()
        self.assertEqual(obj.translated, FieldTranslation({'de-de': 'A value'}))

    def test_empty_translations_to_db(self):
        # Clean removes double entries:
        obj = TranslatedModel(translated={'de-de': 'A value', 'en-gb': '', 'en-us': None})
        obj.full_clean()
        self.assertEqual(obj.translated, {'de-de': 'A value'})

        # It's also not possible to store empty translation in this way:
        TranslatedModel.objects.create(translated={'de-de': 'A value', 'en-gb': '', 'en-us': None})
        raw_obj = RawTranslatedModel.objects.first()
        self.assertEqual(raw_obj.translated, {'de-de': 'A value'})

    def test_create_or_update(self):
        # Create via create_or_update2():
        result = create_or_update2(ModelClass=TranslatedModel, translated={'de-de': 'Hallo'})
        self.assertTrue(result.created)
        instance = result.instance
        self.assertEqual(instance.translated, {'de-de': 'Hallo'})
        self.assertEqual(instance.not_translated, 'A Default Value')

        # Update existing entry:
        result = create_or_update2(
            ModelClass=TranslatedModel,
            lookup=dict(pk=instance.pk),
            translated={'de-de': 'Hallo', 'en-us': 'Hello'},
            not_translated='Not the default.',
        )
        self.assertFalse(result.created)  # updated?
        instance = result.instance
        self.assertEqual(result.updated_fields, ['translated', 'not_translated'])
        self.assertEqual(
            result.update_info,
            [
                FieldUpdate(
                    field_name='translated',
                    old_value=FieldTranslation({'de-de': 'Hallo'}),
                    new_value={'de-de': 'Hallo', 'en-us': 'Hello'},
                ),
                FieldUpdate(field_name='not_translated', old_value='A Default Value', new_value='Not the default.'),
            ],
        )
        self.assertEqual(instance.translated, {'de-de': 'Hallo', 'en-us': 'Hello'})
        self.assertEqual(instance.not_translated, 'Not the default.')

        # We have a special callback to avoid deleting translations:
        result = create_or_update2(
            ModelClass=TranslatedModel,
            lookup=dict(pk=instance.pk),
            update_model_field_callback=create_or_update_translation_callback,
            translated={'de-de': 'Hallo !', 'es': 'Hola'},
        )
        self.assertFalse(result.created)  # updated?
        instance = result.instance
        self.assertEqual(result.updated_fields, ['translated'])
        self.assertEqual(
            result.update_info,
            [
                FieldUpdate(
                    field_name='translated',
                    old_value=FieldTranslation({'de-de': 'Hallo', 'en-us': 'Hello'}),
                    new_value={'de-de': 'Hallo !', 'en-us': 'Hello', 'es': 'Hola'},
                )
            ],
        )
        self.assertEqual(
            instance.translated,
            FieldTranslation(
                {
                    'de-de': 'Hallo !',  # <<< changed
                    'en-us': 'Hello',  # <<< untouched
                    'es': 'Hola',  # <<< added
                }
            ),
        )
        self.assertEqual(instance.not_translated, 'Not the default.')  # unchanged?

    def test_language_codes_order(self):
        language_codes = ('fr-fr', 'de-de', 'en-us')
        model_field = TranslationField(language_codes=language_codes)
        form_field = model_field.formfield()
        self.assertIsInstance(form_field, TranslationFormField)

        widget = form_field.widget
        self.assertIsInstance(widget, TranslationWidget)

        # language_codes pass to the widget?
        self.assertIsInstance(widget.language_codes, tuple)
        self.assertIs(widget.language_codes, language_codes)

        html = widget.render(name='foobar', value=b'{}')

        # Is the order the same as specifies in TranslationField() ?
        self.assertEqual(tuple(re.findall(r'<td>(.{5})</td>', html)), language_codes)
        assert_html_snapshot(got=html, validate=False)

    def test_query(self):
        TranslatedModel.objects.create(translated={'de-de': 'Hallo 1'})
        TranslatedModel.objects.create(translated={'de-de': 'Hallo 2', 'en-us': 'Hello 2'})
        TranslatedModel.objects.create(translated={'de-de': 'Hallo 3', 'en-us': 'Hello 3'})
        self.assertEqual(
            list(TranslatedModel.objects.filter(translated={'de-de': 'Hallo 1'}).values('translated')),
            [{'translated': FieldTranslation({'de-de': 'Hallo 1'})}],
        )

        qs = TranslatedModel.objects.filter(**{'translated__de-de': 'Hallo 1'})
        self.assertEqual(
            list(qs.values('translated')),
            [{'translated': FieldTranslation({'de-de': 'Hallo 1'})}],
        )

        qs = TranslatedModel.objects.order_by('translated').filter(
            Q(**{'translated__de-de': 'Hallo 1'}) | Q(**{'translated__en-us': 'Hello 3'})
        )
        self.assertEqual(
            list(qs.values('translated')),
            [
                {'translated': FieldTranslation({'de-de': 'Hallo 1'})},
                {'translated': FieldTranslation({'de-de': 'Hallo 3', 'en-us': 'Hello 3'})},
            ],
        )


class TranslationAdminTestCase(TestCase):
    # test admin base class and widgets

    def create_test_obj(self):
        obj = TranslatedModel(
            translated={'de-de': 'Zug', 'en-us': 'Train', 'es': 'Tren'},
            translated_multiline={
                'de-de': 'Ein Zug ist sehr schnell.\nZüge können schneller sein als Autos.',
                'en-us': 'A train is very fast.\nTrains can be faster than cars.',
                'es': 'Un tren es muy rápido.\nLos trenes pueden ser más rápidos que los automóviles.',
            },
        )
        obj.full_clean()
        obj.save()
        return obj

    def setUp(self):
        super().setUp()
        self.user = make_test_user(is_superuser=True)
        self.client.force_login(self.user)

    def test_changelist(self):
        obj = self.create_test_obj()

        CODE = 'de-de'
        with translation.override(CODE):
            response = self.client.get('/admin/test_app/translatedmodel/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/html; charset=utf-8')
        response_content = response.content.decode()
        self.assertIn('class="field-get_translated"', response_content)
        self.assertInHTML(obj.translated[CODE], response_content)
        self.assertIn('class="field-get_translated_multiline"', response_content)
        self.assertInHTML(obj.translated_multiline[CODE], response_content)

    def test_change(self):
        obj = self.create_test_obj()

        # view existing record's change form
        response = self.client.get(f'/admin/test_app/translatedmodel/{obj.pk}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/html; charset=utf-8')
        response_content = response.content.decode()

        fieldname = 'translated'
        for code in ['de-de', 'en-us', 'es']:
            self.assertInHTML(
                (
                    f'<input'
                    f' id="id_{fieldname}__{code}"'
                    f' type="text"'
                    f' name="{fieldname}__{code}"'
                    f' value="{getattr(obj, fieldname)[code]}">'
                ),
                response_content,
            )
        fieldname = 'translated_multiline'
        for code in ['de-de', 'en-us', 'es']:
            self.assertInHTML(
                (
                    f'<textarea'
                    f' id="id_{fieldname}__{code}"'
                    f' name="{fieldname}__{code}">'
                    f'{getattr(obj, fieldname)[code]}'
                    f'</textarea>'
                ),
                response_content,
            )

        # change all translations via form
        data = {
            'initial-translated': json.dumps(obj.translated),
            'initial-translated_multiline': json.dumps(obj.translated_multiline),
            'not_translated': 'Foo Bar',
        }
        for code in ['de-de', 'en-us', 'es']:
            data[f'translated__{code}'] = obj.translated[code].upper()
            data[f'translated_multiline__{code}'] = obj.translated_multiline[code].upper()
        response = self.client.post(f'/admin/test_app/translatedmodel/{obj.pk}/change/', data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/html; charset=utf-8')
        messages = response.context['messages']
        self.assertEqual(len(messages), 1)
        self.assertIn('was changed successfully', [str(m) for m in messages][0])

        obj.refresh_from_db()
        self.assertEqual(obj.translated, {'de-de': 'ZUG', 'en-us': 'TRAIN', 'es': 'TREN'})
        self.assertEqual(
            obj.translated_multiline,
            {
                'de-de': 'EIN ZUG IST SEHR SCHNELL.\nZÜGE KÖNNEN SCHNELLER SEIN ALS AUTOS.',
                'en-us': 'A TRAIN IS VERY FAST.\nTRAINS CAN BE FASTER THAN CARS.',
                'es': 'UN TREN ES MUY RÁPIDO.\nLOS TRENES PUEDEN SER MÁS RÁPIDOS QUE LOS AUTOMÓVILES.',
            },
        )

    def test_add(self):
        # attempt to save empty form
        response = self.client.post('/admin/test_app/translatedmodel/add/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/html; charset=utf-8')
        self.assertInHTML(
            '<li>This field is required.</li>',
            response.content.decode(),
            count=2,  # error from blank translated and not_translated TranslatedModel fields
        )
        self.assertEqual(TranslatedModel.objects.count(), 0)

        # save with some data
        data = {
            'initial-translated': '{}',
            'initial-translated_multiline': '{}',
            'not_translated': 'Foo Bar',
            '_continue': 'Save and continue editing',
        }
        for code, field in product(['de-de', 'en-us', 'es'], ['translated', 'translated_multiline']):
            expr = f'{field}__{code}'
            data[expr] = expr
        response = self.client.post('/admin/test_app/translatedmodel/add/', data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/html; charset=utf-8')
        messages = response.context['messages']
        self.assertEqual(len(messages), 1)
        self.assertIn('was added successfully', [str(m) for m in messages][0])

        # was persisted?
        self.assertEqual(TranslatedModel.objects.count(), 1)
        obj = TranslatedModel.objects.first()
        self.assertEqual(
            obj.translated,
            {
                'de-de': 'translated__de-de',
                'en-us': 'translated__en-us',
                'es': 'translated__es',
            },
        )
        self.assertEqual(
            obj.translated_multiline,
            {
                'de-de': 'translated_multiline__de-de',
                'en-us': 'translated_multiline__en-us',
                'es': 'translated_multiline__es',
            },
        )
        self.assertEqual(obj.not_translated, 'Foo Bar')


class SlugUtilsTestCase(SimpleTestCase):
    def test_slug_generator(self):
        slugs = []
        for number, slug in enumerate(slug_generator(source_text='Foo Bar !')):
            slugs.append(slug)
            if number > 2:
                break

        self.assertEqual(slugs, ['foo-bar', 'foo-bar-2', 'foo-bar-3', 'foo-bar-4'])


class TranslationSlugTestCase(TestCase):
    def test_translation_slug_field(self):
        obj = TranslationSlugField(language_codes=('de-de', 'en'), populate_from='foobar')
        value = obj.clean(value={}, model_instance=None)
        self.assertEqual(value, {})

    @override_settings(MAX_UNIQUE_QUERY_ATTEMPTS=3)
    def test_get_unique_translation_slug(self):
        with self.assertRaisesMessage(RuntimeError, 'Can not find a unique slug'):
            for _ in range(4):
                with transaction.atomic():
                    instance = TranslatedSlugTestModel.objects.create(translated={'de-de': 'Hallo !'})

        self.assertEqual(instance.translated_slug, FieldTranslation({'de-de': 'hallo-3'}))

        slugs = list(TranslatedSlugTestModel.objects.values_list('translated_slug', flat=True))
        self.assertEqual(
            slugs,
            [
                FieldTranslation({'de-de': 'hallo'}),
                FieldTranslation({'de-de': 'hallo-2'}),
                FieldTranslation({'de-de': 'hallo-3'}),
            ],
        )

    def test_uniqueness(self):
        instance = TranslatedSlugTestModel(translated={'de-de': 'Hallo !', 'es': 'Hola !'})
        self.assertEqual(instance.translated, {'de-de': 'Hallo !', 'es': 'Hola !'})
        self.assertEqual(instance.translated_slug, FieldTranslation({}))
        instance.full_clean()
        self.assertEqual(instance.translated, {'de-de': 'Hallo !', 'es': 'Hola !'})
        self.assertEqual(instance.translated_slug, FieldTranslation({}))
        instance.save()
        self.assertEqual(instance.translated, {'de-de': 'Hallo !', 'es': 'Hola !'})
        self.assertEqual(instance.translated_slug, FieldTranslation({'de-de': 'hallo', 'es': 'hola'}))

        instance2 = TranslatedSlugTestModel.objects.create(translated={'de-de': 'Hallo !', 'en-us': 'Hello !'})
        self.assertEqual(instance2.translated, {'de-de': 'Hallo !', 'en-us': 'Hello !'})
        self.assertEqual(
            instance2.translated_slug,
            FieldTranslation(
                {
                    'de-de': 'hallo-2',  # <<< not 'hallo' !
                    'en-us': 'hello',
                }
            ),
        )

        instance3 = TranslatedSlugTestModel.objects.create(
            translated={'de-de': 'Hallo !', 'en-us': 'Hello !', 'es': 'Hola !'}
        )
        self.assertEqual(instance3.translated, {'de-de': 'Hallo !', 'en-us': 'Hello !', 'es': 'Hola !'})
        self.assertEqual(
            instance3.translated_slug,
            FieldTranslation(
                {
                    'de-de': 'hallo-3',  # <<< not 'hallo' or 'hallo-2'
                    'en-us': 'hello-2',  # <<< not 'hello'
                    'es': 'hola-2',  # <<< not 'holla'
                }
            ),
        )

    def test_make_existing_slugs_unique(self):
        instance1 = TranslatedSlugTestModel.objects.create(translated_slug={'de-de': 'foo', 'es': '1'})
        self.assertEqual(instance1.translated_slug, {'de-de': 'foo', 'es': '1'})

        instance2 = TranslatedSlugTestModel.objects.create(
            translated_slug={
                'de-de': 'foo',  # <<< e.g.: User has add this slug in admin
                'es': '2',
            }
        )
        self.assertEqual(instance2.translated_slug, {'de-de': 'foo-2', 'es': '2'})

    def test_known_bug(self):
        # With bulk create/update it's possible to make non-unique slugs,
        # if not all translations are the same, e.g.:
        TranslatedSlugTestModel.objects.bulk_create(
            [
                TranslatedSlugTestModel(translated_slug={'de-de': 'foo', 'es': '1'}),
                TranslatedSlugTestModel(translated_slug={'de-de': 'foo', 'es': '2'}),
            ]
        )
        slugs = list(TranslatedSlugTestModel.objects.values_list('translated_slug', flat=True))
        self.assertEqual(
            slugs,
            [
                FieldTranslation({'de-de': 'foo', 'es': '1'}),
                FieldTranslation({'de-de': 'foo', 'es': '2'}),
            ],
        )

        # Unique check on database level will only work if *all* translation are the same, e.g.:
        with self.assertRaisesMessage(IntegrityError, 'UNIQUE constraint failed'):
            TranslatedSlugTestModel.objects.bulk_create(
                [
                    TranslatedSlugTestModel(translated_slug={'de-de': 'same'}),
                    TranslatedSlugTestModel(translated_slug={'de-de': 'same'}),
                ]
            )
