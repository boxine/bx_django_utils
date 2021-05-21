from django.test import TestCase
from django.urls import reverse

from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from bx_django_utils.test_utils.users import make_minimal_test_user


class DynamicViewMenuTestCase(HtmlAssertionMixin, TestCase):
    def test_menu(self):
        minimal_test_user = make_minimal_test_user(
            is_staff=False,
            permissions=()
        )
        self.client.force_login(user=minimal_test_user)

        # User sees the test app model:
        response = self.client.get(path='/')
        self.assert_html_parts(response, parts=(
            '<title>Dynamic View Menu - Index | Django site admin</title>',
            '''
            <div id="content" class="colM">
              <h1>Dynamic View Menu - Index</h1>
            <h2>Section 1</h2>
            <ul>
                <li><a href="/redirect2admin/">Go to Django Admin</a></li>
            </ul>
            <h2>Section 2</h2>
            <ul>
                <li><a href="/demo1/">Dynamic View Menu - DEMO 1</a></li>
                <li><a href="/demo2/">Dynamic View Menu - DEMO 2</a></li>
            </ul>
            <h2>Section 3</h2>
            <ul>
                <li><a href="/demo3/">Dynamic View Menu - DEMO 3</a></li>
            </ul>
              <br class="clear">
            </div>
            '''
        ))

        response = self.client.get(path='/redirect2admin/')
        self.assertRedirects(
            response,
            expected_url='/admin/',
            target_status_code=302  # redirect to login, because we are not a staff user ;)
        )

        response = self.client.get(path='/demo2/')
        self.assert_html_parts(response, parts=(
            '<title>Dynamic View Menu - DEMO 2 | Django site admin</title>',
            '''
            <div id="content" class="colM">
                <h1>Dynamic View Menu - DEMO 2</h1>
                DEMO 2 content
                <br class="clear">
            </div>
            '''
        ))

        # registered with namespace?
        assert reverse('test_app:redirect2admin') == '/redirect2admin/'
        assert reverse('test_app:demo1') == '/demo1/'
