import logging

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from bx_django_utils.admin_extra_views.conditions import only_staff_user
from bx_django_utils.admin_extra_views.datatypes import (
    _APP_LABELS,
    _URL_NAMES,
    AdminExtraMeta,
    PseudoApp,
)
from bx_django_utils.test_utils.html_assertion import (
    HtmlAssertionMixin,
    assert_html_response_snapshot,
)
from bx_django_utils.test_utils.users import make_max_test_user, make_minimal_test_user
from bx_django_utils_tests.test_app.admin_views import (
    DemoView1,
    DemoView3,
    only_john_can_access,
    pseudo_app1,
    pseudo_app2,
)


class DataTypesTestCase(SimpleTestCase):
    def reset(self):
        _APP_LABELS.clear()
        _URL_NAMES.clear()

    def setUp(self) -> None:
        super().setUp()
        self.reset()

    def tearDown(self) -> None:
        super().tearDown()
        self.reset()

    def test_pseudo_app(self):
        PseudoApp(meta=AdminExtraMeta(name='Pseudo App'))

        with self.assertRaisesMessage(
            AssertionError,
            "PseudoApp must be have a unique label! Current label is: 'pseudo-app'",
        ):
            PseudoApp(meta=AdminExtraMeta(name='Pseudo App'))

    def test_unique_urls(self):
        pseudo_app = PseudoApp(meta=AdminExtraMeta(name='Pseudo App'))

        AdminExtraMeta(name='Pseudo Model').setup_app(pseudo_app)

        with self.assertRaisesMessage(
            AssertionError,
            "App label combination 'pseudo-app_pseudo-model' is not unique!",
        ):
            AdminExtraMeta(name='Pseudo Model').setup_app(pseudo_app)


class AdminTestCase(HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        # Has all permissions but is not staff member:
        cls.non_staff_user = make_max_test_user(is_staff=False, exclude_permissions=())

        cls.staff_user = make_minimal_test_user(username='foobar', is_staff=True, permissions=())

        cls.superuser = User.objects.create_superuser(
            username='a-superuser', password='ThisIsNotAPassword!'
        )

    def test_permissions(self):
        # Default condition added?
        self.assertEqual(pseudo_app1.meta.conditions, {only_staff_user})
        self.assertEqual(DemoView1.meta.conditions, {only_staff_user})

        self.assertEqual(DemoView1.meta.url_name, 'pseudo-app-1_demo-view-1')
        url = reverse('pseudo-app-1_demo-view-1')
        self.assertEqual(url, '/admin/pseudo-app-1/demo-view-1/')

        # Anonymous user can't access:
        with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        assert logs.output == [
            "WARNING:bx_django_utils.admin_extra_views.base_view:"
            "User (pk:None) did not pass 'only_staff_user' for 'DemoView1'"
        ]

        # Non-staff users can also not access:
        self.client.force_login(self.non_staff_user)
        with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        assert logs.output == [
            "WARNING:bx_django_utils.admin_extra_views.base_view:"
            f"User (pk:{self.non_staff_user.pk}) did not pass 'only_staff_user' for 'DemoView1'"
        ]

        # Staff user can use the view:
        self.client.force_login(self.staff_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assert_html_parts(
            response,
            parts=('<p>Just the demo view 1</p>',),
        )

    def test_view_inherits_app_conditions(self):
        # App will have default conditions:
        self.assertEqual(pseudo_app2.meta.conditions, {only_staff_user})

        # The app conditions will be added to the view conditions:
        self.assertEqual(DemoView3.meta.conditions, {only_staff_user, only_john_can_access})

    def test_index_page(self):
        app1_demo1 = '<a href="/admin/pseudo-app-1/demo-view-1/">Demo View 1</a>'
        app1_demo2 = '<a href="/admin/pseudo-app-1/demo-view-2/">Demo View 2</a>'
        app2_demo3 = '<a href="/admin/pseudo-app-2/demo-view-3/">Demo View 3</a>'

        ############################################################################
        # A super user sees all pseudo apps/models:
        self.client.force_login(self.superuser)
        response = self.client.get('/admin/')
        self.assert_html_parts(
            response,
            parts=(
                '<title>Site administration | Django site admin</title>',
                (
                    '<a href="" class="section"'
                    ' title="Models in the Pseudo App 2 application">Pseudo App 2</a>'
                ),
                app1_demo1,
                app1_demo2,
                app2_demo3,
            ),
        )
        assert_html_response_snapshot(response, query_selector='#content-main', validate=False)

        ############################################################################
        # Staff user that is not "john" can not see/access demo view 3:
        self.client.force_login(self.staff_user)
        response = self.client.get('/admin/')
        self.assert_html_parts(
            response,
            parts=(
                app1_demo1,
                app1_demo2,
            ),
        )
        self.assert_parts_not_in_html(response, parts=(app2_demo3,))
        with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs:
            response = self.client.get('/admin/pseudo-app-2/demo-view-3/')
        self.assertEqual(response.status_code, 403)
        assert logs.output == [
            "WARNING:bx_django_utils.admin_extra_views.base_view:"
            f"User (pk:{self.staff_user.pk}) did not pass 'only_john_can_access' for 'DemoView3'"
        ]

        ############################################################################
        # Only "john" can see/access demo view 3:
        self.client.force_login(
            make_minimal_test_user(username='john', is_staff=True, permissions=())
        )
        response = self.client.get('/admin/')
        self.assert_html_parts(
            response,
            parts=(
                app1_demo1,
                app1_demo2,
                app2_demo3,
            ),
        )
        response = self.client.get('/admin/pseudo-app-2/demo-view-3/')
        self.assertEqual(response.status_code, 200)
        self.assert_html_parts(
            response,
            parts=("Just the demo view at '/admin/pseudo-app-2/demo-view-3/'",),
        )
