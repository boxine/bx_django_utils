"""
    Use Playwright in Unittest + Fast Django user login
"""
import dataclasses
import os
import warnings

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from playwright.sync_api import Browser, BrowserType, Playwright, sync_playwright


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


@tag('playwright')
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
                    f'Remove setUpTestData() from {cls.__name__} because it will never be called!',
                    stacklevel=2,
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
