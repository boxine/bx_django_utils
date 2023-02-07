import zoneinfo

from bx_py_utils.test_utils.datetime import parse_dt
from django.test import SimpleTestCase, override_settings
from django.utils import timezone, translation

from bx_django_utils.test_utils.html_assertion import assert_html_snapshot
from bx_django_utils.user_timezone.humanize import human_timezone_datetime


@override_settings(VISIBLE_TIMEZONES=['Europe/Berlin', 'America/Los_Angeles'])
class HumanizeTestCase(SimpleTestCase):
    def test_human_timezone_datetime(self):
        with timezone.override(zoneinfo.ZoneInfo('UTC')), translation.override('en'):
            html = human_timezone_datetime(dt=parse_dt('2000-01-01T00:00:00+0000'))
        self.assertIn('Europe/Berlin: Jan. 1, 2000, 1 a.m.', html)
        self.assertIn('America/Los_Angeles: Dec. 31, 1999, 4 p.m.', html)
        self.assertIn('01/01/2000 midnight', html)
        self.assertInHTML('<small>(UTC)</small>', html)
        assert_html_snapshot(got=html, validate=True)

        with timezone.override(zoneinfo.ZoneInfo('Europe/Berlin')), translation.override('de-de'):
            html = human_timezone_datetime(dt=parse_dt('2000-01-01T00:00:00+0000'))
        self.assertIn('Europe/Berlin: 1. Januar 2000 01:00', html)
        self.assertIn('America/Los_Angeles: 31. Dezember 1999 16:00', html)
        self.assertIn('01.01.2000 01:00', html)
        self.assertInHTML('<small>(Europe/Berlin)</small>', html)
        assert_html_snapshot(got=html, validate=True)

        # No <span title=""> without settings.VISIBLE_TIMEZONES:
        with self.settings(VISIBLE_TIMEZONES=[]):
            with timezone.override(zoneinfo.ZoneInfo('Europe/Berlin')), translation.override(
                'de-de'
            ):
                html = human_timezone_datetime(dt=parse_dt('2000-01-01T00:00:00+0000'))
        self.assertHTMLEqual(html, '01.01.2000 01:00<br><small>(Europe/Berlin)</small>')
