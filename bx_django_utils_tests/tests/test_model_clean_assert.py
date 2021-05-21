from django.test import TestCase

from bx_django_utils.test_utils.model_clean_assert import AssertModelCleanCalled
from bx_django_utils_tests.test_app.models import CreateOrUpdateTestModel


class ModelCleanAssertTestCase(TestCase):
    def test_full_clean_called(self):
        with AssertModelCleanCalled() as cm:
            instance = CreateOrUpdateTestModel(name='foo', slug='bar')
            instance.full_clean()
            instance.save()

        cm.assert_no_missing_cleans()
        assert cm.missing_cleans == []
        assert len(cm.called_cleans) == 1
        clean_mock = cm.called_cleans[0]
        assert repr(clean_mock) == '<CleanMock test_app.CreateOrUpdateTestModel>'
        assert clean_mock.clean_called is True

    def test_full_clean_not_called(self):
        with AssertModelCleanCalled() as cm:
            instance = CreateOrUpdateTestModel(name='foo', slug='bar')
            instance.save()

        assert cm.called_cleans == []
        assert len(cm.missing_cleans) == 1
        clean_mock = cm.missing_cleans[0]
        assert repr(clean_mock) == '<CleanMock test_app.CreateOrUpdateTestModel>'
        assert clean_mock.clean_called is False

        with self.assertRaises(AssertionError) as err:
            cm.assert_no_missing_cleans()

        error_msg = str(err.exception)
        assert 'There are 1 missing clean calls:' in error_msg
        assert 'test_app.CreateOrUpdateTestModel:' in error_msg

        # The stack:
        assert __file__ in error_msg
        assert 'in test_full_clean_not_called' in error_msg
