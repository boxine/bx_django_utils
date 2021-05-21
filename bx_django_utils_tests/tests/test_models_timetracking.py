import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from bx_django_utils_tests.test_app.models import TimetrackingTestModel


class TimetrackingMixinTestCase(TestCase):
    def test_timetracking(self):
        item = TimetrackingTestModel()

        mocked_dt1 = datetime.datetime(2000, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc)
        with mock.patch.object(timezone, 'now', return_value=mocked_dt1):
            item.save()
        item = TimetrackingTestModel.objects.get(pk=item.pk)
        assert item.create_dt == mocked_dt1
        assert item.update_dt == mocked_dt1

        mocked_dt2 = datetime.datetime(2000, 1, 2, 4, 4, 5, tzinfo=datetime.timezone.utc)
        with mock.patch.object(timezone, 'now', return_value=mocked_dt2):
            item.save()
        item = TimetrackingTestModel.objects.get(pk=item.pk)
        assert item.create_dt == mocked_dt1
        assert item.update_dt == mocked_dt2

        mocked_dt3 = datetime.datetime(2000, 1, 2, 5, 4, 5, tzinfo=datetime.timezone.utc)
        with mock.patch.object(timezone, 'now', return_value=mocked_dt3):
            item.save(update_dt=False)
            item = TimetrackingTestModel.objects.get(pk=item.pk)
            assert item.create_dt == mocked_dt1
            assert item.update_dt == mocked_dt2
            item.save(update_dt=True, update_fields=())
        item = TimetrackingTestModel.objects.get(pk=item.pk)
        assert item.create_dt == mocked_dt1
        assert item.update_dt == mocked_dt3
