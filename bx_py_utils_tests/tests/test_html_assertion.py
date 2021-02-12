from django.contrib import messages
from django.contrib.messages.storage.session import SessionStorage
from django.test import RequestFactory, SimpleTestCase

from bx_py_utils.test_utils.html_assertion import HtmlAssertionMixin


class FakeResponse:
    def __init__(self, request):
        self.wsgi_request = request


def get_request():
    request = RequestFactory().request()
    request.session = {}
    request._messages = SessionStorage(request)
    return request


class HtmlAssertionTestCase(HtmlAssertionMixin, SimpleTestCase):
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
            '  [\n'
            '      "First message.",\n'
            '-     "Second message.",\n'
            '+     "Second X message.",\n'
            '?            ++\n'
            '\n'
            '      "The last message."\n'
            '  ]'
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assert_messages(response, expected_messages=[
                'First message.',
                'Second X message.',
                'The last message.'
            ])
