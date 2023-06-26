import json

from django import template


register = template.Library()


@register.filter
def json_encode(value):
    return json.dumps(value)
