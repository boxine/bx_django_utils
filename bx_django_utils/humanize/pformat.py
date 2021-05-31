import pprint

from django.core.serializers.json import DjangoJSONEncoder


def pformat(value):
    """
    Better `pretty-print-format` using `DjangoJSONEncoder` with fallback to `pprint.pformat()`

    Try to use JSON fist, because it nicer than pprint.pformat() ;)
    Use DjangoJSONEncoder, because it can encode additional types like:
        date/time, decimal types, UUIDs
    """
    try:
        value = DjangoJSONEncoder(indent=4, sort_keys=True, ensure_ascii=False).encode(value)
    except TypeError:
        # Fallback if values are not serializable with JSON:
        value = pprint.pformat(value, width=120)

    return value
