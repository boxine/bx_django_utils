import datetime
from unittest.mock import patch

from bx_py_utils.test_utils.datetime import parse_dt
from django.test import SimpleTestCase
from django.utils import timezone, translation

from bx_django_utils.templatetags.humanize_time import human_duration


class HumanizeTimeTestCase(SimpleTestCase):
    @translation.override('en')
    def test_mixed(self):
        # convert mixed offset-naive and offset-aware times:
        foo_dt = parse_dt('2000-01-01T12:00:00+0000')
        assert timezone.is_aware(foo_dt), f'{foo_dt=}'

        result = human_duration(value=timezone.make_naive(foo_dt), arg=foo_dt)
        self.assertEqual(result, '<span title="Jan. 1, 2000, noon">0.0\xa0ms</span>')

        result = human_duration(value=foo_dt, arg=timezone.make_naive(foo_dt))
        self.assertEqual(result, '<span title="Jan. 1, 2000, noon">0.0\xa0ms</span>')

    @translation.override('en')
    def test_basic(self):
        result = human_duration(
            parse_dt('2000-01-01T12:00:00+0000'),
            parse_dt('2000-01-01T12:10:00+0000'),
        )
        self.assertEqual(result, '<span title="Jan. 1, 2000, noon">10.0\xa0minutes</span>')

        result = human_duration(
            parse_dt('2000-01-01T12:00:00+0000'),
            parse_dt('2000-01-01T12:00:02+0000'),
        )
        self.assertEqual(result, '<span title="Jan. 1, 2000, noon">2.0\xa0seconds</span>')

        with translation.override('de'):
            result = human_duration(
                parse_dt('2000-01-01T12:00:00+0000'),
                parse_dt('2000-01-01T12:10:00+0000'),
            )
            self.assertEqual(result, '<span title="1. Januar 2000 12:00">10.0\xa0Minuten</span>')

        result = human_duration(
            parse_dt('2000-01-01T12:32:12+0000'),
            parse_dt('2000-01-01T12:20:10+0000'),
        )
        self.assertEqual(result, '<span title="Jan. 1, 2000, 12:32 p.m.">-12.0\xa0minutes</span>')

        years_back = timezone.now() - datetime.timedelta(days=5 * 365)
        result = human_duration(years_back)
        assert result.endswith('>5.0\xa0years</span>'), f'{result=}'

        result = human_duration(
            datetime.date(2000, 1, 1),
            datetime.date(2000, 6, 15),
        )
        self.assertEqual(result, '<span title="Jan. 1, 2000, midnight">5.5\xa0months</span>')

        # Mock timezone.now should work:
        now = parse_dt('2000-01-01T00:00:00+0000')
        with patch.object(timezone, 'now', return_value=now):
            result = human_duration(now)
        self.assertEqual(result, '<span title="Jan. 1, 2000, midnight">0.0\xa0ms</span>')

        # Check error handling:
        self.assertEqual(human_duration(None), '')
        self.assertEqual(human_duration(value=object), '')
