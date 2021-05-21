import re
import string


_LOWERCASES = string.ascii_lowercase + 'äöüß'
_UPPERCASES = string.ascii_uppercase + 'ÄÖÜẞ'
_OTHER = ' ' + string.punctuation
_ANONYMIZATION_TRANS = str.maketrans(
    _LOWERCASES + _UPPERCASES + string.digits + _OTHER,
    'x' * len(_LOWERCASES) + 'X' * len(_UPPERCASES) + '#' * len(string.digits) + '_' * len(_OTHER)
)
_RE_OTHER = re.compile(r'[^xX_\.\s/-]')


def anonymize(value: str) -> str:
    """
    >>> anonymize('Foo Bar')
    'Fxx_Xxr'
    >>> anonymize('This is a Test 123 Foo Bar #+"-! End')
    'Txxx_xx_x_Xxxx_###_Xxx_Xxx_______Xxd'
    >>> anonymize('a.mail-address@test.tld')
    'a_xxxx_xxxxxxs@test.tld'
    """
    assert isinstance(value, str)

    if '@' in value:
        value, at, domain = value.partition('@')
        if len(value) < 2:
            return value + at + domain

        return (
            value[:1] +
            _RE_OTHER.sub('@', value[1:-1].translate(_ANONYMIZATION_TRANS)) +
            value[-1:] +
            at + domain
        )

    value = f'{value[:1]}{value[1:-1].translate(_ANONYMIZATION_TRANS)}{value[-1:]}'
    return value
