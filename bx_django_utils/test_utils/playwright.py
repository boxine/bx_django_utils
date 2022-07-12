"""
    Use Playwright in Pytest and Unittest + Fast Django user login
"""
import os

import pytest
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.client import Client
from playwright.sync_api import Browser, BrowserType, Page, Playwright, sync_playwright


def setup_browser_context_args(context: dict) -> dict:
    """
    Change Playwright browser arguments: Ignore https errors and `locale=en_US`
    """
    # The StaticLiveServerTestCase server doesn't have a valid certificate:
    context['ignore_https_errors'] = True

    # Explicitly set the browser language. Imported for e.g.: date time input fields:
    context['locale'] = 'en_US'

    return context


def fast_login(page: Page, client: Client, live_server_url: str, user: AbstractUser) -> None:
    """
    Helper to fast login, by injecting the session cookie.
    Usage, e.g.:
        fast_login(
            page=self.page,
            client=self.client,
            user=User.objects.create_superuser(username='a-user', password='ThisIsNotAPassword!'),
            live_server_url=self.live_server_url,
        )
    """
    # Create a session by using Django's test login:
    client.force_login(user=user)
    session_cookie = client.cookies[settings.SESSION_COOKIE_NAME]
    assert session_cookie

    # Inject the session Cookie to playwright browser:
    cookie_object = {
        'name': session_cookie.key,
        'value': session_cookie.value,
        'url': live_server_url,
    }
    page.context.add_cookies([cookie_object])


class UnittestRunnerMixin:
    """
    Mixin to initialize Playwright if Unittest runner is used.
    Note: All pytest CLI arguments [1] are not supported here!
    [1] https://playwright.dev/python/docs/test-runners#cli-arguments
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        if 'PYTEST_CURRENT_TEST' not in os.environ:
            # Unittest runner is used -> We have to setup Playwright manually:
            playwright: Playwright = sync_playwright().start()
            browser_type: BrowserType = playwright.chromium
            browser: Browser = browser_type.launch()
            browser_context_args = {}
            setup_browser_context_args(browser_context_args)
            context = browser.new_context(**browser_context_args)
            cls.page = context.new_page()


@pytest.mark.playwright
class PyTestPlaywrightBaseTestCase(UnittestRunnerMixin, StaticLiveServerTestCase):
    """
    Base class for classed based Playwright tests, using pytest or Unittest runner.

      * Based on Django's StaticLiveServerTestCase.
      * Setup a Playwright Page instance via pytest fixtures or by UnittestRunnerMixin
      * Mark all tests with "playwright".
      * Implement setUpTestData() call
    """

    @classmethod
    def setUpTestData(cls):
        """Load initial data for the TestCase."""
        pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpTestData()

    @pytest.fixture(autouse=True)
    def setup_pytest_fixture(self, page: Page):
        self.page = page

    def login(self, user: AbstractUser) -> None:
        """
        Helper to fast login, by injecting the session cookie.
        """
        fast_login(
            page=self.page, client=self.client, live_server_url=self.live_server_url, user=user
        )
