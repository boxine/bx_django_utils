from unittest import mock

from django.template.defaulttags import CsrfTokenNode
from django.test import TestCase

from bx_django_utils.test_utils.html_assertion import (
    HtmlAssertionMixin,
    assert_html_response_snapshot,
)
from bx_django_utils.test_utils.users import make_test_user


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
