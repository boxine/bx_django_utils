import datetime

from django.template import Library
from django.utils import dateformat
from django.utils.formats import get_format
from django.utils.html import format_html
from django.utils.timezone import is_aware, utc

from bx_django_utils.humanize.time import human_timedelta


register = Library()


@register.filter
def human_duration(value, arg=None):
    """
    Verbose time since template tag, e.g.: `<span title="Jan. 1, 2000, noon">2.0 seconds</span>`

    e.g.:
        <span title="Jan. 1, 2000, noon">2.0 seconds</span>
    """
    if not value:
        return ''

    try:
        # Convert datetime.date to datetime.datetime for comparison.
        if not isinstance(value, datetime.datetime):
            value = datetime.datetime(value.year, value.month, value.day)

        if arg and not isinstance(arg, datetime.datetime):
            arg = datetime.datetime(arg.year, arg.month, arg.day)

        arg = arg or datetime.datetime.now(utc if is_aware(value) else None)

        delta_str = human_timedelta(t=arg - value)
        time_str = dateformat.format(value, get_format('DATETIME_FORMAT'))
    except (AttributeError, ValueError, TypeError):
        return ''

    return format_html(
        '<span title="{time_str}">{delta_str}</span>',
        time_str=time_str,
        delta_str=delta_str,
    )
