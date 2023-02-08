import zoneinfo

from bx_py_utils.test_utils.datetime import parse_dt
from django.template import Context, Template
from django.test import SimpleTestCase
from django.utils import timezone, translation

from bx_django_utils.test_utils.html_assertion import assert_html_snapshot


TEST_TEMPLATE = """\
{% load user_timezone %}
Datetime: {{ dt|humane_timezone_dt }}.
"""


class HumanizeTestCase(SimpleTestCase):
    def test_humane_timezone_dt(self):
        template = Template(TEST_TEMPLATE)

        with timezone.override(zoneinfo.ZoneInfo('UTC')), translation.override('en'):
            context = Context({'dt': parse_dt('2000-01-01T00:00:00+0000')})
            html = template.render(context)
        self.assertIn('Europe/Berlin: Jan. 1, 2000, 1 a.m.', html)
        self.assertIn('America/Los_Angeles: Dec. 31, 1999, 4 p.m.', html)
        self.assertIn('01/01/2000 midnight', html)
        self.assertInHTML('<small>(UTC)</small>', html)
        assert_html_snapshot(got=html, validate=False)

        with timezone.override(zoneinfo.ZoneInfo('Europe/Berlin')), translation.override('de-de'):
            context = Context({'dt': parse_dt('2000-01-01T00:00:00+0000')})
            html = template.render(context)
        self.assertIn('Europe/Berlin: 1. Januar 2000 01:00', html)
        self.assertIn('America/Los_Angeles: 31. Dezember 1999 16:00', html)
        self.assertIn('01.01.2000 01:00', html)
        self.assertInHTML('<small>(Europe/Berlin)</small>', html)
        assert_html_snapshot(got=html, validate=False)
