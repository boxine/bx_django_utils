import requests
import requests_mock
from django.test import SimpleTestCase

from bx_py_utils.test_utils.requests_mock_assertion import assert_json_requests_mock


class RequestsMockAssertionTestCase(SimpleTestCase):
    def test_basic(self):
        with requests_mock.mock() as m:
            m.post('http://test.tld', text='resp')
            requests.post('http://test.tld', json={'foo': 'bar'})

        assert_json_requests_mock(mock=m, data=[{
            'request': 'POST http://test.tld/',
            'json': {'foo': 'bar'},
        }])

    def test_no_valid_json(self):
        with requests_mock.mock() as m:
            m.post('http://test.tld', text='resp')
            requests.post('http://test.tld', data='This it no JSON !')

        msg = (
            "POST http://test.tld/ without valid JSON:"
            " Expecting value: line 1 column 1 (char 0) in:\n"
            "'This it no JSON !'"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            assert_json_requests_mock(mock=m, data=[{
                'request': 'POST https://foo.tld/bar/',
                'json': {'req': 'one'},
            }])

    def test(self):
        with requests_mock.mock() as m:
            m.post(
                'https://foo.tld/bar/',
                response_list=[
                    {'json': {'info': '1'}, },
                    {'json': {'info': '2'}, },
                ]
            )
            requests.post(
                url='https://foo.tld/bar/',
                json={'req': 'one'}
            )
            requests.post(
                url='https://foo.tld/bar/',
                json={'req': 'two'}
            )

        assert_json_requests_mock(mock=m, data=[{
            'request': 'POST https://foo.tld/bar/',
            'json': {'req': 'one'},
        }, {
            'request': 'POST https://foo.tld/bar/',
            'json': {'req': 'two'},
        }])

        msg = (
            'Request history are not equal:\n'
            '--- got\n'
            '\n'
            '+++ expected\n'
            '\n'
            '@@ -7,7 +7,7 @@\n'
            '\n'
            '     },\n'
            '     {\n'
            '         "json": {\n'
            '-            "req": "two"\n'
            '+            "req": "XXX"\n'
            '         },\n'
            '         "request": "POST https://foo.tld/bar/"\n'
            '     }'
        )
        with self.assertRaisesMessage(AssertionError, msg):
            assert_json_requests_mock(mock=m, data=[{
                'request': 'POST https://foo.tld/bar/',
                'json': {'req': 'one'},
            }, {
                'request': 'POST https://foo.tld/bar/',
                'json': {'req': 'XXX'},
            }])
