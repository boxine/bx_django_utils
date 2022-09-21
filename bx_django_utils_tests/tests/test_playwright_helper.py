from django.contrib.auth.models import User
from playwright.sync_api import BrowserContext, expect

from bx_django_utils.test_utils.playwright import PlaywrightTestCase


class TestPlaywrightTestCase(PlaywrightTestCase):

    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_superuser(
            username='a-superuser',
            password='ThisIsNotAPassword!',
        )

    def test_login(self):
        context: BrowserContext = self.browser.new_context(
            ignore_https_errors=True,  # StaticLiveServerTestCase has no valid certificate ;)
            locale='en-US',
        )
        with context.new_page() as page:
            # Redirect to login?
            page.goto(f'{self.live_server_url}/admin/')
            expect(page).to_have_url(f'{self.live_server_url}/admin/login/?next=/admin/')
            expect(page).to_have_title('Log in | Django site admin')

            # Login:
            page.fill('#id_username', 'a-superuser')
            page.fill('#id_password', 'ThisIsNotAPassword!')
            page.keyboard.press('Enter')

            # Are we logged in?
            expect(page).to_have_url(f'{self.live_server_url}/admin/')
            expect(page).to_have_title('Site administration | Django site admin')


class TestWithFirefoxTestCase(PlaywrightTestCase):
    BROWSER_NAME = 'firefox'

    def test_browser(self):
        self.assertEqual(self.browser_name, 'firefox')
        self.assertEqual(self.browser_type.name, 'firefox')


class TestWithChromiumTestCase(PlaywrightTestCase):
    BROWSER_NAME = 'chromium'

    def test_browser(self):
        self.assertEqual(self.browser_name, 'chromium')
        self.assertEqual(self.browser_type.name, 'chromium')
