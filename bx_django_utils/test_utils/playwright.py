"""
    Use Playwright in Pytest and Unittest + Fast Django user login
"""
import dataclasses
import os
import warnings

import pytest
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.client import Client
from playwright.sync_api import Browser, BrowserType, Page, Playwright, sync_playwright


def setup_browser_context_args(context: dict) -> dict:
    """
    DEPRECATED: Will be removed in the future! Use new "PlaywrightTestCase"

    Change Playwright browser arguments: Ignore https errors and `locale=en_US`
    """
    warnings.warn(
        'setup_browser_context_args() is deprecated and will removed in the future!',
        DeprecationWarning,
    )

    # The StaticLiveServerTestCase server doesn't have a valid certificate:
    context['ignore_https_errors'] = True

    # Explicitly set the browser language. Imported for e.g.: date time input fields:
    context['locale'] = 'en_US'

    return context


def fast_login(page: Page, client: Client, live_server_url: str, user: AbstractUser) -> None:
    """
    DEPRECATED: Will be removed in the future! Use new "PlaywrightTestCase"

    Helper to fast login, by injecting the session cookie.
    Usage, e.g.:
        fast_login(
            page=self.page,
            client=self.client,
            user=User.objects.create_superuser(username='a-user', password='ThisIsNotAPassword!'),
            live_server_url=self.live_server_url,
        )
    """
    warnings.warn(
        'PyTestPlaywrightBaseTestCase is deprecated and will removed in the future!',
        DeprecationWarning,
    )

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
    DEPRECATED: Will be removed in the future! Use new "PlaywrightTestCase"

    Mixin to initialize Playwright if Unittest runner is used.
    Note: All pytest CLI arguments [1] are not supported here!
    [1] https://playwright.dev/python/docs/test-runners#cli-arguments
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        if 'PYTEST_CURRENT_TEST' not in os.environ:
            warnings.warn(
                'UnittestRunnerMixin is deprecated and will removed in the future!',
                DeprecationWarning,
            )

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
    DEPRECATED: Will be removed in the future! Use new "PlaywrightTestCase"

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
        warnings.warn(
            'PyTestPlaywrightBaseTestCase is deprecated, please use PlaywrightTestCase',
            DeprecationWarning,
        )
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


@dataclasses.dataclass
class PlaywrightConfig:
    """
    PlaywrightTestCase config from environment (PWBROWSER, PWHEADLESS, PWSKIP, PWSLOWMO)
    """

    browser_name: str  # Browser to launch: "chromium", "firefox" or "webkit"
    headless: bool  # whether to show the browser during test execution or not
    skip: bool  # whether to skip all Playwright tests or not
    slow_mo: int  # add a delay in microseconds between every interaction

    @classmethod
    def from_env(cls):
        return cls(
            browser_name=os.environ.get('PWBROWSER', 'chromium'),
            headless=bool(int(os.environ.get('PWHEADLESS', '1'))),
            skip=bool(int(os.environ.get('PWSKIP', '0'))),
            slow_mo=int(os.environ.get('PWSLOWMO', '0')),
        )


@pytest.mark.playwright
class PlaywrightTestCase(StaticLiveServerTestCase):
    """
    StaticLiveServerTestCase with helpers for writing frontend tests using Playwright.

    Example usage:

        class MyFrontendTestCase(PlaywrightTestCase):
            def test_foobar(self):
                context = self.browser.new_context(ignore_https_errors=True)
                with context.new_page() as page:
                    page.goto(f'{self.live_server_url}/foo/bar')
                    expect(page).to_have_title('My Site')
    """

    # Optional: Used browser for this test case.
    # If this is set, the environment variable "PWBROWSER" will be ignored.
    # Possible names are: "chromium", "firefox" or "webkit"
    BROWSER_NAME = None

    @classmethod
    def setUpClass(cls):
        """
        Launch Playwright browser init with config from environment.
        """
        super().setUpClass()

        cls.pw_config = PlaywrightConfig.from_env()

        # skip init if "PWSKIP=1" in environment:
        if not cls.pw_config.skip:
            cls.playwright: Playwright = sync_playwright().start()
            cls.browser_name: str = cls.BROWSER_NAME or cls.pw_config.browser_name
            cls.browser_type: BrowserType = getattr(cls.playwright, cls.browser_name)
            cls.browser: Browser = cls.browser_type.launch(
                headless=cls.pw_config.headless,
                slow_mo=cls.pw_config.slow_mo,
            )

            if hasattr(cls, 'setUpTestData'):
                warnings.warn(
                    f'Remove setUpTestData() from {cls.__name__}'
                    ' because it will never be called!'
                )

    @classmethod
    def tearDownClass(cls):
        if not cls.pw_config.skip:
            cls.browser.close()
            cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        super().setUp()

        # skip this test if "PWSKIP=1" in environment:
        if self.pw_config.skip:
            self.skipTest('Playwright tests are excluded')
