from bx_py_utils.test_utils.snapshot import assert_snapshot
from django import forms
from django.http import HttpResponse
from django.test import TestCase

from bx_django_utils.test_utils.forms import AssertFormFields


class TestUtilsFormsTestCase(TestCase):
    def test_assert_form_fields(self):
        response = self.client.get(path='/admin/login/')

        # Are we on the login page?
        self.assertTemplateUsed(response, 'admin/login.html')

        # Check the form fields:
        assert_form_fields = AssertFormFields(response)
        self.assertEqual(assert_form_fields.get_all_field_names(), {'password', 'username'})
        self.assertGreaterEqual(len(assert_form_fields), 2)

        assert_form_fields.assert_field_names_not_exists(field_names={'internal', 'foo', 'bar'})
        with self.assertRaisesMessage(
            AssertionError, "These fields should not occur, but are present: 'username'"
        ):
            assert_form_fields.assert_field_names_not_exists(
                field_names={'not-exists1', 'username', 'not-exists2'}
            )

        assert_form_fields.assert_field_names_exists(field_names={'password', 'username'})
        with self.assertRaisesMessage(
            AssertionError, "Fields: 'not-exists' are not present in: 'password', 'username'"
        ):
            assert_form_fields.assert_field_names_exists(
                field_names={'password', 'not-exists', 'username'}
            )
        assert_snapshot(got=assert_form_fields.data)

    def test_assert_form_fields_gets_all_field_types(self):
        class TestForm(forms.Form):
            a_input_field = forms.CharField(max_length=123)
            a_hidden_input_field = forms.CharField(widget=forms.HiddenInput)
            a_select_field = forms.ChoiceField(choices=(('foo', 'foo'), ('bar', 'bar')))
            a_textarea = forms.CharField(widget=forms.Textarea)

        content = TestForm().as_p()
        content = f'<div id="content"><form>{content}</form></div>'
        response = HttpResponse(content=f'{content}'.encode())
        assert_form_fields = AssertFormFields(response)
        all_field_names = assert_form_fields.get_all_field_names()
        self.assertEqual(all_field_names, {'a_input_field', 'a_select_field', 'a_textarea'})
