import datetime
from unittest import mock
from unittest.mock import patch

from bx_py_utils.test_utils.datetime import parse_dt
from django.contrib.admin.models import LogEntry
from django.template.defaulttags import CsrfTokenNode
from django.test import TestCase
from django.utils import timezone

from bx_django_utils.feature_flags.test_utils import (
    FeatureFlagTestCaseMixin,
    get_feature_flag_db_info,
    get_feature_flag_states,
)
from bx_django_utils.templatetags.humanize_time import human_duration
from bx_django_utils.test_utils.datetime import MockDatetimeGenerator
from bx_django_utils.test_utils.html_assertion import (
    HtmlAssertionMixin,
    assert_html_response_snapshot,
    get_django_name_suffix,
)
from bx_django_utils.test_utils.users import make_test_user
from bx_django_utils_tests.test_app.feature_flags import bar_feature_flag, foo_feature_flag


class FeatureFlagIntegrationTestCase(FeatureFlagTestCaseMixin, HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.superuser = make_test_user(username='test-superuser', is_superuser=True)

    @patch.object(timezone, 'now', MockDatetimeGenerator(datetime.timedelta(minutes=1)))
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
                '<h2 id="foo">Foo - ENABLED&nbsp;<a href="#foo">&para;</a></h2>',
                '<input type="submit" value="Set \'Foo\' to DISABLED">',
                '<h2 id="bar">Bar - DISABLED&nbsp;<a href="#bar">&para;</a></h2>',
                '<input type="submit" value="Set \'Bar\' to ENABLED">',
            ),
        )
        assert_html_response_snapshot(
            response,
            query_selector='#content',
            validate=False,
            name_suffix=get_django_name_suffix(),
        )

        self.assertEqual(foo_feature_flag.state.name, 'ENABLED')
        self.assertEqual(bar_feature_flag.state.name, 'DISABLED')
        self.assert_messages(response, expected_messages=[])

        response = self.client.get('/admin/feature_flags/feature-flags-values-demo/')
        self.assertRedirects(response, expected_url='/admin/', fetch_redirect_response=False)
        self.assert_messages(
            response,
            expected_messages=[
                'Demo Feature "Foo" state: ENABLED',
                'Demo Feature "Bar" state: DISABLED',
            ],
        )

        self.client = self.get_fresh_client()  # "Clear" messages by recreate test client

        response = self.client.post(
            '/admin/feature_flags/manage/',
            data={
                'cache_key': 'feature-flags-foo',
                'new_value': '1',
            },
        )
        self.assert_messages(response, expected_messages=['Current "Foo" state is already: ENABLED'])
        self.assertRedirects(
            response,
            expected_url='/admin/feature_flags/manage/',
            fetch_redirect_response=False,
            msg_prefix=response.content.decode('utf-8'),
        )
        self.assertEqual(LogEntry.objects.count(), 0)

        self.client = self.get_fresh_client()  # "Clear" messages by recreate test client

        response = self.client.post(
            '/admin/feature_flags/manage/',
            data={
                'cache_key': 'feature-flags-foo',
                'new_value': '0',
            },
        )
        self.assert_messages(response, expected_messages=['Set "Foo" to DISABLED'])
        self.assertRedirects(
            response,
            expected_url='/admin/feature_flags/manage/',
            fetch_redirect_response=False,
            msg_prefix=response.content.decode('utf-8'),
        )
        log_entry = LogEntry.objects.get()
        self.assertEqual(log_entry.change_message, 'Changed feature flag "Foo"')
        self.assertEqual(log_entry.object_repr, 'Set "Foo" to DISABLED')
        self.assertEqual(log_entry.object_id, 'feature-flags-foo')

        self.assertTrue(log_entry.action_time)  # Time is set?

        # "Mock" the real time:
        action_time = parse_dt('2000-06-15T00:00:00+0000')
        LogEntry.objects.update(action_time=action_time)

        with (patch.object(CsrfTokenNode, 'render', return_value='MockedCsrfTokenNode'),):
            response = self.client.get('/admin/feature_flags/manage/')
        self.assert_html_parts(
            response,
            parts=(
                '<h2 id="foo">Foo - DISABLED&nbsp;<a href="#foo">&para;</a></h2>',
                '<h2 id="bar">Bar - DISABLED&nbsp;<a href="#bar">&para;</a></h2>',
                f'<p>Last changed by test-superuser {human_duration(action_time)} ago.</p>',
            ),
        )
        assert_html_response_snapshot(response, query_selector='#content', validate=False)


class PersistentFeatureFlagTestCase(FeatureFlagTestCaseMixin, TestCase):
    warum_up_feature_flag_cache = False

    def test_persistent(self):
        # Nothing stored, yet:
        self.assertEqual(get_feature_flag_db_info(), {})

        # Check initial state of "Foo"-Flag:
        self.assertTrue(foo_feature_flag.is_enabled)  # Foo initial == enabled

        # Check will persistent the current stage of the flag:
        self.assertEqual(get_feature_flag_db_info(), {'feature-flags-foo': 1})

        # Check initial state of "Bar"-Flag:
        self.assertFalse(bar_feature_flag.is_enabled)  # Bar initial == disabled

        # Now both are persistent:
        self.assertEqual(get_feature_flag_db_info(), {'feature-flags-bar': 0, 'feature-flags-foo': 1})
        # Check get_feature_flag_states():
        self.assertEqual(get_feature_flag_states(), {'feature-flags-bar': False, 'feature-flags-foo': True})

        # toggle flags:
        foo_feature_flag.disable()
        self.assertEqual(get_feature_flag_states(), {'feature-flags-bar': False, 'feature-flags-foo': False})
        bar_feature_flag.enable()
        self.assertEqual(get_feature_flag_states(), {'feature-flags-bar': True, 'feature-flags-foo': False})

        # Check state:
        self.assertFalse(foo_feature_flag.is_enabled)
        self.assertTrue(bar_feature_flag.is_enabled)

        self.assertEqual(get_feature_flag_db_info(), {'feature-flags-bar': 1, 'feature-flags-foo': 0})

        # State should be not changed:
        self.assertFalse(foo_feature_flag.is_enabled)
        self.assertTrue(bar_feature_flag.is_enabled)
        self.assertEqual(get_feature_flag_db_info(), {'feature-flags-bar': 1, 'feature-flags-foo': 0})

    def test_temp_enable(self):
        self.assertTrue(foo_feature_flag)
        self.assertFalse(bar_feature_flag)

        with (
            foo_feature_flag.temp_enable(),
            bar_feature_flag.temp_enable(),
        ):
            self.assertTrue(foo_feature_flag)
            self.assertTrue(bar_feature_flag)

        self.assertTrue(foo_feature_flag)
        self.assertFalse(bar_feature_flag)

    def test_temp_disable(self):
        self.assertTrue(foo_feature_flag)
        self.assertFalse(bar_feature_flag)

        with (
            foo_feature_flag.temp_disable(),
            bar_feature_flag.temp_disable(),
        ):
            self.assertFalse(foo_feature_flag)
            self.assertFalse(bar_feature_flag)

        self.assertTrue(foo_feature_flag)
        self.assertFalse(bar_feature_flag)
