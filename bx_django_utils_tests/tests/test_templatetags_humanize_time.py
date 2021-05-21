import datetime

from bx_py_utils.test_utils.datetime import parse_dt
from django.test import SimpleTestCase
from django.utils import translation

from bx_django_utils.templatetags.humanize_time import human_duration


class HumanizeTimeTestCase(SimpleTestCase):
    def test_basic(self):
        with translation.override('en'):
            result = human_duration(
                parse_dt('2000-01-01T12:00:00+0000'),
                parse_dt('2000-01-01T12:10:00+0000'),
            )
            assert result == '<span title="Jan. 1, 2000, noon">10.0\xa0minutes</span>'

        with translation.override('en'):
            result = human_duration(
                parse_dt('2000-01-01T12:00:00+0000'),
                parse_dt('2000-01-01T12:00:02+0000'),
            )
            assert result == '<span title="Jan. 1, 2000, noon">2.0\xa0seconds</span>'

        with translation.override('de'):
            result = human_duration(
                parse_dt('2000-01-01T12:00:00+0000'),
                parse_dt('2000-01-01T12:10:00+0000'),
            )
            assert result == '<span title="1. Januar 2000 12:00">10.0\xa0minutes</span>'

        with translation.override('en'):
            result = human_duration(
                parse_dt('2000-01-01T12:32:12+0000'),
                parse_dt('2000-01-01T12:20:10+0000'),
            )
            assert result == '<span title="Jan. 1, 2000, 12:32 p.m.">-12.0\xa0minutes</span>'

        with translation.override('en'):
            years_back = datetime.datetime.now() - datetime.timedelta(days=5 * 365)
            result = human_duration(years_back)
            assert result.endswith('>5.0\xa0years</span>')

        assert human_duration(None) == ''
        assert human_duration(value=object) == ''

        with translation.override('en'):
            result = human_duration(
                datetime.date(2000, 1, 1),
                datetime.date(2000, 6, 15),
            )
            assert result == '<span title="Jan. 1, 2000, midnight">5.5\xa0months</span>'
