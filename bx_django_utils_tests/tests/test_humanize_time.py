import datetime

from django.test import SimpleTestCase
from django.utils import translation

from bx_django_utils.humanize.time import human_timedelta


class HumanizeTimeTestCase(SimpleTestCase):
    def test_basic(self):
        with translation.override('en'):
            assert human_timedelta(datetime.timedelta(microseconds=2500)) == '2.5\xa0ms'
            assert human_timedelta(datetime.timedelta(microseconds=-5250)) == '-5.2\xa0ms'

            assert human_timedelta(2.5) == '2.5\xa0seconds'
            assert human_timedelta(-10.3) == '-10.3\xa0seconds'

            assert human_timedelta(datetime.timedelta(days=5 * 365)) == '5.0\xa0years'
            assert human_timedelta(-datetime.timedelta(days=5 * 365)) == '-5.0\xa0years'

        with translation.override('de'):
            assert human_timedelta(datetime.timedelta(microseconds=2500)) == '2.5\xa0ms'
            assert human_timedelta(2.5) == '2.5\xa0Sekunden'
            assert human_timedelta(datetime.timedelta(days=3, hours=12)) == '3.5\xa0Tage'
            assert human_timedelta(datetime.timedelta(days=5 * 365)) == '5.0\xa0Jahre'
