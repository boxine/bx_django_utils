import datetime
import decimal
import uuid
from collections.abc import Callable
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import Promise

DJANGO_JSON_ENCODER_TYPES = (  # All types that DjangoJSONEncoder will convert
    datetime.datetime, datetime.date, datetime.time, datetime.timedelta,
    decimal.Decimal, uuid.UUID, Promise
)
JSON_SERIALIZEABLE_TYPES = (  # Without list, tuple, dict
    bool, str, int, float,
)
ALL_SERIALIZEABLE_TYPES = JSON_SERIALIZEABLE_TYPES + DJANGO_JSON_ENCODER_TYPES


def make_json_serializable(value: Any, convert_func: Callable = repr) -> Any:
    """
    Convert value to a JSON serializable value, with convert callback for special objects.
    Leave data types like datetime, UUID untouched, because DjangoJSONEncoder will handle this.
    """
    if value is None:
        return None
    elif isinstance(value, (set, list, tuple)):
        return [make_json_serializable(item, convert_func) for item in value]
    elif isinstance(value, dict):
        return {
            make_json_serializable(key, convert_func): make_json_serializable(value, convert_func)
            for key, value in value.items()
        }
    elif isinstance(value, ALL_SERIALIZEABLE_TYPES):
        return value

    return convert_func(value)


def to_json(
        value: Any,
        sort_keys=True,
        ensure_ascii=False,
        convert_func: Callable = repr,
        **json_kwargs
):
    """
    Convert value to JSON via make_json_serializable() and DjangoJSONEncoder()
    """
    value = make_json_serializable(value, convert_func=convert_func)
    value = DjangoJSONEncoder(
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        **json_kwargs
    ).encode(value)
    return value
