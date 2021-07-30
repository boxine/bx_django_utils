from django.core.exceptions import ValidationError
from django.test import TestCase

from bx_django_utils_tests.test_app.models import ColorFieldTestModel


class ColorFieldTestCase(TestCase):
    def test_model(self):
        instance = ColorFieldTestModel(required_color='#00AAff')
        instance.full_clean()
        assert instance.required_color == '#00AAff'
        assert instance.optional_color is None

        instance = ColorFieldTestModel(required_color='#00XX00')
        msg = "{'required_color': ['Enter a valid seven-character hexadecimal color value.']}"
        with self.assertRaisesMessage(ValidationError, msg):
            instance.full_clean()

        instance = ColorFieldTestModel(required_color='#11223')
        msg = (
            "{'required_color': ['Ensure this value has at least 7 characters (it has 6).',"
            " 'Enter a valid seven-character hexadecimal color value.']}"
        )
        with self.assertRaisesMessage(ValidationError, msg):
            instance.full_clean()

        instance = ColorFieldTestModel(required_color='#1122334')
        msg = (
            "{'required_color': ['Ensure this value has at most 7 characters (it has 8).',"
            " 'Enter a valid seven-character hexadecimal color value.']}"
        )
        with self.assertRaisesMessage(ValidationError, msg):
            instance.full_clean()
