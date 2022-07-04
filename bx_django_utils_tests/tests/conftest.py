import pytest

from bx_django_utils.test_utils.playwright import setup_browser_context_args


@pytest.fixture(scope='session')
def browser_context_args(browser_context_args):
    setup_browser_context_args(browser_context_args)
    return browser_context_args
