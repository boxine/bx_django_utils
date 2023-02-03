from unittest import mock

from django.core.cache import cache
from django.template.defaulttags import CsrfTokenNode
from django.test import TestCase

from bx_django_utils.feature_flags.models import FeatureFlagModel
from bx_django_utils.test_utils.cache import ClearCacheMixin
from bx_django_utils.test_utils.html_assertion import (
    HtmlAssertionMixin,
    assert_html_response_snapshot,
)
from bx_django_utils.test_utils.users import make_test_user
from bx_django_utils_tests.test_app.feature_flags import bar_feature_flag, foo_feature_flag


class FeatureFlagIntegrationTestCase(HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.superuser = make_test_user(is_superuser=True)

    def test_basic(self):
        self.client.force_login(self.superuser)
        response = self.client.get('/admin/')
        self.assert_html_parts(
            response,
            parts=(
                '<a href="/admin/feature_flags/manage/">Manage Feature Flags</a>',
                (
                    '<a href="/admin/feature_flags/feature-flags-values-demo/">'
                    'Feature Flags values DEMO</a>'
                ),
            ),
        )

        with mock.patch.object(CsrfTokenNode, 'render', return_value='MockedCsrfTokenNode'):
            response = self.client.get('/admin/feature_flags/manage/')
        self.assert_html_parts(
            response,
            parts=(
                '<h2>Foo - ENABLED</h2>',
                '<input type="submit" value="Set \'Foo\' to DISABLED">',
                '<h2>Bar - DISABLED</h2>',
                '<input type="submit" value="Set \'Bar\' to ENABLED">',
            ),
        )
        assert_html_response_snapshot(response, query_selector='#content', validate=False)

        response = self.client.get('/admin/feature_flags/feature-flags-values-demo/')
        self.assertRedirects(response, expected_url='/admin/', fetch_redirect_response=False)
        self.assert_messages(
            response,
            expected_messages=[
                'Demo Feature "Foo" state: ENABLED',
                'Demo Feature "Bar" state: DISABLED',
            ],
        )


class PersistantFeatureFlagTestCase(ClearCacheMixin, TestCase):
    def get_db_states(self):
        return list(
            FeatureFlagModel.objects.order_by('cache_key').values_list('cache_key', 'state')
        )

    def get_cache_states(self):
        result = []
        for flag in (bar_feature_flag, foo_feature_flag):
            cache_key = flag.cache_key
            value = cache.get(cache_key)
            if value is not None:
                result.append((cache_key, value))
        return result

    def test_peristant(self):
        # Nothing stored, yet:
        self.assertEqual(self.get_cache_states(), [])
        self.assertEqual(self.get_db_states(), [])

        # Check initial state:
        self.assertTrue(foo_feature_flag.is_enabled)  # Foo initial == enabled
        self.assertFalse(bar_feature_flag.is_enabled)  # Bar initial == disabled

        # Nothing stored, yet:
        self.assertEqual(self.get_cache_states(), [])
        self.assertEqual(self.get_db_states(), [])

        # toggle flags:
        foo_feature_flag.disable()
        self.assertEqual(self.get_cache_states(), [('feature-flags-foo', 0)])
        self.assertEqual(self.get_db_states(), [('feature-flags-foo', 0)])
        bar_feature_flag.enable()
        self.assertEqual(
            self.get_cache_states(),
            [('feature-flags-bar', 1), ('feature-flags-foo', 0)],
        )
        self.assertEqual(
            self.get_db_states(),
            [('feature-flags-bar', 1), ('feature-flags-foo', 0)],
        )

        # Check state:
        self.assertFalse(foo_feature_flag.is_enabled)
        self.assertTrue(bar_feature_flag.is_enabled)

        # Remove the states from the cache:
        cache.clear()

        # Cache empty, but database holds still the data:
        self.assertEqual(self.get_cache_states(), [])
        self.assertEqual(self.get_db_states(), [('feature-flags-bar', 1), ('feature-flags-foo', 0)])

        # State should be not changed:
        self.assertFalse(foo_feature_flag.is_enabled)
        self.assertTrue(bar_feature_flag.is_enabled)

        # Now it's in the cache:
        self.assertEqual(
            self.get_cache_states(),
            [('feature-flags-bar', 1), ('feature-flags-foo', 0)],
        )
        self.assertEqual(
            self.get_db_states(),
            [('feature-flags-bar', 1), ('feature-flags-foo', 0)],
        )
