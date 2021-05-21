from django.core.exceptions import ValidationError
from django.test import TestCase
from stdnum.exceptions import InvalidChecksum, InvalidFormat, InvalidLength

from bx_django_utils.data_types.gtin.constants import DEFAULT_ACCEPT_LENGTH
from bx_django_utils.data_types.gtin.form_fields import GtinFormField
from bx_django_utils.data_types.gtin.validators import GtinValidator, validate_gtin
from bx_django_utils_tests.test_app.models import GtinFieldTestModel


TEST_DATA = (
    '98412345678908',  # EAN-14
    '9783453059078',  # EAN-13 / ISBN-13
    '692771981161',  # UPC (12-digit)
    '3453059077',  # ISBN-10
    '73513537',  # EAN-8
)
NOT_VALID_TEST_DATA = (
    '10000000000000',  # EAN-14
    '1000000000000',  # EAN-13 / ISBN-13
    '100000000000',  # UPC (12-digit)
    '1000000000',  # ISBN-10
    '10000000',  # EAN-8
)


def iter_test_data():
    for number in TEST_DATA:
        length = len(number)
        yield (number, length)


def iter_not_valid_test_data():
    for number in NOT_VALID_TEST_DATA:
        length = len(number)
        yield (number, length)


class ValidatorTestCase(TestCase):
    def test_validate_gtin(self):
        for number, length in iter_test_data():
            validated_number = validate_gtin(number, accepted_length=(length,))
            assert validated_number == number

            with self.assertRaisesMessage(InvalidFormat, 'The number has an invalid format.'):
                validate_gtin('X' * length, accepted_length=(length,))

        err_msg = "The number's checksum or check digit is invalid."
        for number, length in iter_not_valid_test_data():
            with self.assertRaisesMessage(InvalidChecksum, err_msg):
                validate_gtin(number, accepted_length=(length,))

        for number, length in iter_test_data():
            if length in DEFAULT_ACCEPT_LENGTH:
                validated_number = validate_gtin(number)
                assert validated_number == number

            with self.assertRaisesMessage(InvalidLength, 'The number has an invalid length.'):
                validate_gtin(number='123')

    def test_GtinValidator(self):
        for number, length in iter_test_data():
            validator = GtinValidator(accepted_length=(length,))
            validator(number)

        default_validator = GtinValidator()
        for number, length in iter_test_data():
            if length in DEFAULT_ACCEPT_LENGTH:
                default_validator(number)

    def test_validator_eq(self):
        validator1 = GtinValidator()
        validator2 = GtinValidator(accepted_length=(8,))
        validator3 = GtinValidator(accepted_length=DEFAULT_ACCEPT_LENGTH)
        assert validator1 != validator2
        assert validator1 == validator3


class GtinFormFieldTestCase(TestCase):
    def test_basic(self):
        for number, length in iter_test_data():
            field = GtinFormField(accepted_length=(length,))
            field.clean(number)
            with self.assertRaisesMessage(ValidationError, 'The number has an invalid format.'):
                field.clean('X' * length)

        err_msg = 'The number\'s checksum or check digit is invalid.'
        field = GtinFormField(accepted_length=(8, 10, 12, 13, 14))
        for number in NOT_VALID_TEST_DATA:
            with self.assertRaisesMessage(ValidationError, err_msg):
                field.clean(number)

        assert field.prepare_value('978-3-453-05907-9') == '9783453059079'


class GtinFieldTestModelTestCase(TestCase):
    def test_basic(self):
        instance = GtinFieldTestModel.objects.create(
            default_gtin='692771981161',  # UPC (12-digit)
            all_gtin='98412345678908',  # EAN-14
            ean13='9783453059078',  # EAN-13 / ISBN-13
        )
        instance.full_clean()

        # Our model field used our form field?
        model_field = instance._meta.get_field('default_gtin')
        form_field = model_field.formfield()
        assert isinstance(form_field, GtinFormField)

        err_msg = 'The number has an invalid format.'
        for number, length in iter_test_data():
            instance.all_gtin = number
            if length in DEFAULT_ACCEPT_LENGTH:
                instance.default_gtin = number
            if length == 13:
                instance.ean13 = number
            instance.full_clean()

            instance.all_gtin = 'X' * length
            with self.assertRaisesMessage(ValidationError, err_msg):
                instance.full_clean()

        err_msg = '{\'all_gtin\': ["The number\'s checksum or check digit is invalid."]}'
        for number in NOT_VALID_TEST_DATA:
            instance.all_gtin = number
            with self.assertRaisesMessage(ValidationError, err_msg):
                instance.full_clean()

    def test_none_value(self):
        instance = GtinFieldTestModel.objects.create(
            default_gtin='692771981161',  # required
            all_gtin='',  # blank=True, null=False
            ean13=None,  # null=True, blank=True,
        )
        instance.full_clean()

        all_gtin_form_field = instance._meta.get_field('all_gtin').formfield()
        assert all_gtin_form_field.clean(None) == ''
        assert all_gtin_form_field.clean('') == ''
        assert all_gtin_form_field.prepare_value(None) is None
        assert all_gtin_form_field.prepare_value('') == ''

        ean13_form_field = instance._meta.get_field('ean13').formfield()
        assert ean13_form_field.clean(None) is None
        assert ean13_form_field.clean('') is None
        assert ean13_form_field.prepare_value(None) is None
        assert ean13_form_field.prepare_value('') == ''
