from pathlib import Path

from bx_py_utils.test_utils.assertion import assert_equal
from bx_py_utils.test_utils.snapshot import assert_html_snapshot, assert_snapshot
from django.contrib.messages import get_messages
from django.http import HttpResponse


def assert_html_response_snapshot(
    response: HttpResponse,
    status_code=200,
    query_selector='#content',
    **kwargs
):
    """
    Assert a HttpResponse via snapshot file using assert_html_snapshot() from bx_py_utils.
    Defaults to the `#content` container. Make sure to specify your own `query_selector=''` if you
    need to test other parts of the HTML document.
    e.g.:
        response = self.client.get(path='/foo/bar/')
        assert_html_response_snapshot(response, validate=False)

    Hint: Validation will fail with default Django admin templates.
    """
    if response.content:  # e.g.: 302 has no content
        html = response.content.decode('utf-8')
        assert_html_snapshot(
            got=html,
            self_file_path=Path(__file__),
            query_selector=query_selector,
            **kwargs
        )
    assert response.status_code == status_code, (
        f'Status code is {response.status_code} but excepted {status_code}'
    )


class HtmlAssertionMixin:
    """
    Unittest mixin class with useful assertments around Django test client tests
    """

    def assert_messages(self, response, expected_messages):
        current_messages = [m.message for m in get_messages(response.wsgi_request)]
        assert_equal(
            current_messages,
            expected_messages,
            msg='Messages are not equal:'
        )

    def snapshot_messages(self, response, **kwargs):
        current_messages = [m.message for m in get_messages(response.wsgi_request)]
        assert_snapshot(got=current_messages, self_file_path=Path(__file__), **kwargs)

    def get_msg_prefix_and_haystack(self, response, msg_prefix):
        haystack = response.content.decode('utf-8')
        haystack_striped = '\n'.join(line for line in haystack.splitlines() if line.strip())
        msg_prefix = (
            f'\n{"-"*100}\n'
            f'{haystack_striped}'
            f'\n{"-"*100}\n'
            f'{msg_prefix}'
        )
        return msg_prefix, haystack

    def assert_html_language(self, response, language_code):
        """
        Note: django/contrib/admin/templates/admin/base.html will generate this:

            <html lang="en-gb" >

        Pay attention to the space! So self.assertInHTML() can't be used here :(
        """
        haystack = response.content.decode('utf-8')
        assert f'<html lang="{language_code}"' in haystack

    def pformat_response(self, response):
        html = response.content.decode('utf-8')
        html = '\n'.join(
            f'{no:04} {line}' for no, line in enumerate(html.splitlines(), 1)
        )
        return html

    def assert_html_parts(self, response, parts, msg_prefix=''):
        assert isinstance(parts, (tuple, list)), \
            f'Invalid parts argument {parts!r} of type {type(parts).__name__}'

        msg_prefix, haystack = self.get_msg_prefix_and_haystack(response, msg_prefix=msg_prefix)
        for needle in parts:
            try:
                if '<' in needle:
                    self.assertInHTML(
                        needle=needle, haystack=haystack, msg_prefix=msg_prefix
                    )
                else:
                    # Simple text search
                    assert needle in haystack
            except AssertionError as err:
                if 'Second argument is not valid HTML' in err.args[0]:
                    # error e.g.:
                    #
                    #       Second argument is not valid HTML:
                    #       ('Unexpected end tag `br` (Line 155, Column 84)', (155, 84))
                    #
                    # Display a html listing with line numbers for easy debugging:
                    #
                    html = self.pformat_response(response)
                    msg = (
                        f'\n{"-"*100}\n'
                        f'{html}'
                        f'\n{"-"*100}\n'
                        f'{err}'
                    )
                    raise AssertionError(msg)
                raise

    def assert_parts_not_in_html(self, response, parts, msg_prefix=''):
        assert isinstance(parts, (tuple, list)), \
            f'Invalid parts argument {parts!r} of type {type(parts).__name__}'

        msg_prefix, haystack = self.get_msg_prefix_and_haystack(response, msg_prefix=msg_prefix)
        for needle in parts:
            self.assertNotIn(needle, haystack, msg=f'{msg_prefix} {needle!r} found!')

    def assert_redirects(
            self,
            response,
            expected_url,
            msg_prefix='',
            fetch_redirect_response=False,
            **kwargs):

        msg_prefix, haystack = self.get_msg_prefix_and_haystack(response, msg_prefix=msg_prefix)
        self.assertRedirects(
            response,
            expected_url=expected_url,
            msg_prefix=msg_prefix,
            fetch_redirect_response=fetch_redirect_response,
            **kwargs
        )
