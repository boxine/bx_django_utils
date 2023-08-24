import json
import pathlib
import tempfile
from unittest import mock

from bx_py_utils.environ import OverrideEnviron
from bx_py_utils.test_utils.redirect import RedirectOut
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.session import SessionStorage
from django.template.defaulttags import CsrfTokenNode
from django.test import RequestFactory, TestCase

from bx_django_utils.test_utils.html_assertion import (
    HtmlAssertionMixin,
    assert_html_response_snapshot,
    get_django_name_suffix,
)
from bx_django_utils.test_utils.users import make_test_user


class FakeResponse:
    def __init__(self, request):
        self.wsgi_request = request


def get_request():
    request = RequestFactory().request()
    request.session = {}
    request._messages = SessionStorage(request)
    return request


class HtmlAssertionTestCase(HtmlAssertionMixin, TestCase):
    def test_assert_messages(self):
        request = get_request()
        messages.info(request, 'First message.')
        messages.warning(request, 'Second message.')
        messages.error(request, 'The last message.')
        response = FakeResponse(request)
        self.assert_messages(response, expected_messages=[
            'First message.',
            'Second message.',
            'The last message.'
        ])

        msg = (
            'Messages are not equal:\n'
            '--- got\n'
            '\n'
            '+++ expected\n'
            '\n'
            '@@ -1,5 +1,5 @@\n'
            '\n'
            ' [\n'
            '     "First message.",\n'
            '-    "Second message.",\n'
            '+    "Second X message.",\n'
            '     "The last message."\n'
            ' ]'
        )
        with self.assertRaisesMessage(AssertionError, msg), RedirectOut() as buffer:
            self.assert_messages(response, expected_messages=[
                'First message.',
                'Second X message.',
                'The last message.'
            ])

        self.assertEqual(
            buffer.stdout.strip('- \n'),
            "['First message.', 'Second message.', 'The last message.']",
        )

    def test_get_current_user(self):
        self.assertEqual(self.get_current_user(), AnonymousUser())

        user = make_test_user(is_superuser=True)
        self.client.force_login(user)

        self.assertEqual(self.get_current_user(), user)

    def test_get_fresh_client(self):
        origin_client_id = id(self.client)
        self.client = self.get_fresh_client()
        self.assertIsInstance(self.client, self.client_class)
        self.assertNotEqual(id(self.client), origin_client_id)
        self.assertEqual(self.get_current_user(), AnonymousUser())

        # "Transfer" the current user:
        user = make_test_user(is_superuser=True)
        self.client.force_login(user)
        self.client = self.get_fresh_client()
        self.assertEqual(self.get_current_user(), user)

    def test_snapshot_messages(self):
        request = get_request()
        messages.info(request, 'First message.')
        messages.warning(request, 'Second message.')
        messages.error(request, 'The last message.')
        response = FakeResponse(request)

        with tempfile.TemporaryDirectory() as tmp_dir, OverrideEnviron(
            RAISE_SNAPSHOT_ERRORS='1'  # Maybe it's disabled in this test run!
        ), self.assertRaises(FileNotFoundError):
            self.snapshot_messages(response, root_dir=tmp_dir)

            # Test that snapshot got written
            snapshot_name = 'test_html_assertion_snapshot_messages_1'
            snapshot_file = (pathlib.Path(tmp_dir) / f'{snapshot_name}.snapshot.json')
            snapshot_content = json.loads(snapshot_file.read_text())
            self.assertEqual(
                snapshot_content, ['First message.', 'Second message.', 'The last message.'])

            # Should work now
            self.snapshot_messages(response, root_dir=tmp_dir, snapshot_name=snapshot_name)

    def test_assert_html_response_snapshot(self):
        with mock.patch.object(CsrfTokenNode, 'render', return_value='MockedCsrfTokenNode'):
            assert_html_response_snapshot(
                response=self.client.get(path='/admin/login/'),
                status_code=200,
                validate=False,
                query_selector=None,
                name_suffix=get_django_name_suffix(),
            )

        response = self.client.get(path='/admin/')
        self.assertRedirects(
            response, expected_url='/admin/login/?next=%2Fadmin%2F', fetch_redirect_response=False
        )

        # A redirect has no content, so no snapshot file will be created,
        # but the status code is checked, too:
        assert_html_response_snapshot(response, status_code=302, validate=False, query_selector=None)

        msg = 'Status code is 302 but excepted 200'
        with self.assertRaisesMessage(AssertionError, msg):
            assert_html_response_snapshot(response, validate=False, query_selector=None)
