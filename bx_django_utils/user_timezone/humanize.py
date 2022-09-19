import datetime

from django.conf import settings
from django.template.loader import render_to_string


def human_timezone_datetime(dt):
    """
    Render a datetime with timezone information.
    """
    if not dt:
        return '-'
    assert isinstance(dt, datetime.datetime)
    context = {
        'dt': dt,
        'timezones': settings.VISIBLE_TIMEZONES,
    }
    return render_to_string(
        template_name='user_timezone/human_timezone_datetime.html',
        context=context,
    )
