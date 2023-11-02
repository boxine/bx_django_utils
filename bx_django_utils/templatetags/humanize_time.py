from __future__ import annotations

import datetime

from django.template import Library
from django.utils import dateformat, timezone
from django.utils.formats import get_format
from django.utils.html import format_html

from bx_django_utils.humanize.time import human_timedelta


register = Library()


@register.filter
def human_duration(
    value: datetime.date | datetime.datetime | None,
    arg: datetime.date | datetime.datetime | None = None,
):
    """
    Verbose time since template tag, e.g.: `<span title="Jan. 1, 2000, noon">2.0 seconds</span>`

    e.g.:
        <span title="Jan. 1, 2000, noon">2.0 seconds</span>

    value and arg can be datetime.datetime or datetime.date.
    and can be timezone aware or naive.
    """
    if not value:
        return ''

    try:
        # Convert datetime.date to datetime.datetime for comparison.
        if not isinstance(value, datetime.datetime):
            value = datetime.datetime(value.year, value.month, value.day)

        if arg is None:
            arg = timezone.now()
        elif not isinstance(arg, datetime.datetime):
            arg = datetime.datetime(arg.year, arg.month, arg.day)

        if timezone.is_aware(value) and timezone.is_naive(arg):
            value = timezone.make_naive(value)

        if timezone.is_naive(value) and timezone.is_aware(arg):
            arg = timezone.make_naive(arg)

        delta_str = human_timedelta(t=arg - value)
        time_str = dateformat.format(value, get_format('DATETIME_FORMAT'))
    except (AttributeError, ValueError, TypeError):
        return ''

    return format_html(
        '<span title="{time_str}">{delta_str}</span>',
        time_str=time_str,
        delta_str=delta_str,
    )
