import json
import re
from itertools import product

from django.test import TestCase
from django.utils import translation

from bx_django_utils.test_utils.users import make_test_user
from bx_django_utils_tests.test_app.models import TranslatedModel


class TranslationFieldTestCase(TestCase):
    def test_stores_only_wanted_languages(self):
        obj = TranslatedModel(
            translated={'de-de': 'Hallo', 'en-us': 'Hello', 'es': 'Hola', 'it': 'Ciao'},
            translated_multiline={'de-de': 'Hallo', 'en-us': 'Hello', 'es': 'Hola', 'it': 'Ciao'},
        )
        obj.full_clean()

        # italian translation should not be in the database because it wasn't listed
        # as language code in the field definition on the model
        self.assertEqual(obj.translated, {'de-de': 'Hallo', 'en-us': 'Hello', 'es': 'Hola'})
        self.assertEqual(obj.translated_multiline, {'de-de': 'Hallo', 'en-us': 'Hello', 'es': 'Hola'})


class TranslationAdminTestCase(TestCase):
    # test admin base class and widgets

    def setUp(self):
        super().setUp()
        self.user = make_test_user(is_superuser=True)
        self.obj = TranslatedModel(
            translated={'de-de': 'Zug', 'en-us': 'Train', 'es': 'Tren'},
            translated_multiline={
                'de-de': 'Ein Zug ist sehr schnell.\nZüge können schneller sein als Autos.',
                'en-us': 'A train is very fast.\nTrains can be faster than cars.',
                'es': 'Un tren es muy rápido.\nLos trenes pueden ser más rápidos que los automóviles.',
            },
        )
        self.obj.full_clean()
        self.obj.save()
        self.client.force_login(self.user)

    def test_changelist(self):
        CODE = 'de-de'
        with translation.override(CODE):
            response = self.client.get('/admin/test_app/translatedmodel/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/html; charset=utf-8')
        response_content = response.content.decode()
        self.assertIn('class="field-get_translated"', response_content)
        self.assertInHTML(self.obj.translated[CODE], response_content)
        self.assertIn('class="field-get_translated_multiline"', response_content)
        self.assertInHTML(self.obj.translated_multiline[CODE], response_content)

    def test_change(self):
        # view existing record's change form
        response = self.client.get(f'/admin/test_app/translatedmodel/{self.obj.pk}/change/')
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
                    f' value="{getattr(self.obj, fieldname)[code]}">'
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
                    f'{getattr(self.obj, fieldname)[code]}'
                    f'</textarea>'
                ),
                response_content,
            )

        # change all translations via form
        data = {
            'initial-translated': json.dumps(self.obj.translated),
            'initial-translated_multiline': json.dumps(self.obj.translated_multiline),
        }
        for code in ['de-de', 'en-us', 'es']:
            data[f'translated__{code}'] = self.obj.translated[code].upper()
            data[f'translated_multiline__{code}'] = self.obj.translated_multiline[code].upper()
        response = self.client.post(f'/admin/test_app/translatedmodel/{self.obj.pk}/change/', data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/html; charset=utf-8')
        messages = response.context['messages']
        self.assertEqual(len(messages), 1)
        self.assertIn('was changed successfully', [str(m) for m in messages][0])

        self.obj.refresh_from_db()
        self.assertEqual(self.obj.translated, {'de-de': 'ZUG', 'en-us': 'TRAIN', 'es': 'TREN'})
        self.assertEqual(
            self.obj.translated_multiline,
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
            count=1,  # error from blank TranslatedModel.translated
        )

        # save with some data
        data = {
            'initial-translated': '{}',
            'initial-translated_multiline': '{}',
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
        id_ = re.search('[0-9]+', response.request['PATH_INFO']).group()
        obj = TranslatedModel.objects.get(id=int(id_))
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
