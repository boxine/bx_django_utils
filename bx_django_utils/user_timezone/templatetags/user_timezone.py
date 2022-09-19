from django import template

from bx_django_utils.user_timezone.humanize import human_timezone_datetime


register = template.Library()


@register.filter
def humane_timezone_dt(value):
    """
    Template filter to render a datetime with timezone information.
    """
    return human_timezone_datetime(dt=value)
