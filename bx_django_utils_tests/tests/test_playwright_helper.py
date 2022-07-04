from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpRequest
from playwright.sync_api import Page, expect

from bx_django_utils.test_utils.playwright import PyTestPlaywrightBaseTestCase


class PlaywrightTestHelperTestCase(PyTestPlaywrightBaseTestCase):
    def test_setup_pytest_fixture(self):
        assert hasattr(self, 'page')
        page = self.page
        assert isinstance(page, Page)

    def test_admin_login(self):
        # Create a User:
        username = 'a-user'
        password = 'ThisIsNotAPassword!'
        superuser = User.objects.create_superuser(username=username, password=password)
        superuser.full_clean()

        # Use can login?
        user = authenticate(request=HttpRequest(), username=username, password=password)
        assert isinstance(user, User)

        # Redirect to login?
        self.page.goto(f'{self.live_server_url}/admin/')
        expect(self.page).to_have_url(f'{self.live_server_url}/admin/login/?next=/admin/')
        expect(self.page).to_have_title('Log in | Django site admin')

        # Login:
        self.page.type('#id_username', username)
        self.page.type('#id_password', password)
        self.page.locator('text=Log in').click()

        # Are we logged in?
        expect(self.page).to_have_url(f'{self.live_server_url}/admin/')
        expect(self.page).to_have_title('Site administration | Django site admin')

    def test_fast_login(self):
        user = User.objects.create_superuser(username='a-user', password='ThisIsNotAPassword!')
        self.login(user)

        # Are we logged in?
        self.page.goto(f'{self.live_server_url}/admin/')
        expect(self.page).to_have_url(f'{self.live_server_url}/admin/')
        expect(self.page).to_have_title('Site administration | Django site admin')
