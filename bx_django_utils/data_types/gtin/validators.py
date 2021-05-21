from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from stdnum import isbn
from stdnum.ean import calc_check_digit, compact
from stdnum.exceptions import InvalidChecksum, InvalidFormat, InvalidLength
from stdnum.exceptions import ValidationError as StdnumValidationError
from stdnum.util import isdigits

from bx_django_utils.data_types.gtin.constants import DEFAULT_ACCEPT_LENGTH


def validate_gtin(number, accepted_length=DEFAULT_ACCEPT_LENGTH):
    """
    It's the same as stdnum.ean.validate() but also accept ISBN-10
    """
    number = compact(number)  # Convert to the minimal representation
    if not isdigits(number):
        raise InvalidFormat()

    if len(number) not in accepted_length:
        raise InvalidLength()

    if len(number) == 10:
        # Maybe a ISBN-10 number:
        return isbn.validate(number)

    if calc_check_digit(number[:-1]) != number[-1]:
        raise InvalidChecksum()

    return number


@deconstructible
class GtinValidator:
    """ Validate GTIN number """

    code = 'invalid'

    def __init__(self, accepted_length=DEFAULT_ACCEPT_LENGTH):
        self.accepted_length = accepted_length

    def __call__(self, value):
        try:
            validate_gtin(value, accepted_length=self.accepted_length)
        except StdnumValidationError as err:
            raise ValidationError(err.message, code=self.code)

    def __eq__(self, other):
        return (
            isinstance(other, GtinValidator) and
            self.accepted_length == other.accepted_length
        )
