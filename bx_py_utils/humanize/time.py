import datetime

from django.utils.html import avoid_wrapping
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy


TIMESINCE_CHUNKS = (
    (60 * 60 * 24 * 365, gettext_lazy('%.1f years')),
    (60 * 60 * 24 * 30, gettext_lazy('%.1f months')),
    (60 * 60 * 24 * 7, gettext_lazy('%.1f weeks')),
    (60 * 60 * 24, gettext_lazy('%.1f days')),
    (60 * 60, gettext_lazy('%.1f hours')),
    (60, gettext_lazy('%.1f minutes')),
)


def human_timedelta(t):
    """
    Converts a time duration into a friendly text representation.

    >>> human_timedelta(datetime.timedelta(microseconds=1000))
    '1.0\xa0ms'
    >>> human_timedelta(0.01)
    '10.0\xa0ms'
    >>> human_timedelta(0.9)
    '900.0\xa0ms'
    >>> human_timedelta(datetime.timedelta(seconds=1))
    '1.0\xa0seconds'
    >>> human_timedelta(65.5)
    '1.1\xa0minutes'
    >>> human_timedelta(59 * 60)
    '59.0\xa0minutes'
    >>> human_timedelta(60*60)
    '1.0\xa0hours'
    >>> human_timedelta(1.05*60*60)
    '1.1\xa0hours'
    >>> human_timedelta(datetime.timedelta(hours=24))
    '1.0\xa0days'
    >>> human_timedelta(2.54 * 60 * 60 * 24 * 365)
    '2.5\xa0years'
    >>> human_timedelta('type error')
    Traceback (most recent call last):
        ...
    TypeError: human_timedelta() argument must be timedelta, integer or float)
    """
    if isinstance(t, datetime.timedelta):
        t = t.total_seconds()
    elif not isinstance(t, (int, float)):
        raise TypeError('human_timedelta() argument must be timedelta, integer or float)')

    if abs(t) < 1:
        return avoid_wrapping(_('%.1f ms') % round(t * 1000, 1))
    if abs(t) < 60:
        return avoid_wrapping(_('%.1f seconds') % round(t, 1))

    for seconds, time_string in TIMESINCE_CHUNKS:
        count = t / seconds
        if abs(count) >= 1:
            count = round(count, 1)
            break

    return avoid_wrapping(time_string % count)


human_timedelta.is_safe = True
