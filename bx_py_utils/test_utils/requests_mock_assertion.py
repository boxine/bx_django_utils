from json import JSONDecodeError

from bx_py_utils.test_utils.assertion import assert_equal


def assert_json_requests_mock(mock, data):
    """
    Check the requests history.
    e.g.:

        with requests_mock.mock() as m:
            m.post('http://test.tld', text='resp')
            requests.post('http://test.tld', json={'foo': 'bar'})

        assert_json_requests_mock(mock=m, data=[{
            'request': 'POST http://test.tld/',
            'json': {'foo': 'bar'},
        }])
    """
    history = []
    for request in mock.request_history:
        request_info = f'{request.method} {request.url}'
        try:
            json_data = request.json()
        except JSONDecodeError as err:
            raise AssertionError(f'{request_info} without valid JSON: {err} in:\n{err.doc!r}')

        history.append({
            'request': request_info,
            'json': json_data
        })

    assert_equal(history, data, msg='Request history are not equal:')
