import io
import logging

from bx_py_utils.test_utils.log_utils import NoLogs
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from django.views import View

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.checks import admin_extra_views_check
from bx_django_utils.admin_extra_views.conditions import only_staff_user
from bx_django_utils.admin_extra_views.datatypes import _APP_LABELS, _URL_NAMES, AdminExtraMeta, PseudoApp
from bx_django_utils.admin_extra_views.management.commands import admin_extra_views
from bx_django_utils.admin_extra_views.registry import extra_view_registry, register_admin_view
from bx_django_utils.admin_extra_views.site import ExtraViewAdminSite
from bx_django_utils.admin_extra_views.utils import reverse_admin_extra_view
from bx_django_utils.admin_extra_views.views import Redirect2AdminExtraView
from bx_django_utils.test_utils.html_assertion import (
    HtmlAssertionMixin,
    assert_html_response_snapshot,
    get_django_name_suffix,
)
from bx_django_utils.test_utils.users import make_max_test_user, make_minimal_test_user
from bx_django_utils_tests.test_app.admin_views import (
    DemoView1,
    DemoView2,
    DemoView3,
    only_john_can_access,
    pseudo_app1,
    pseudo_app2,
)


class ClearDataTypesInfoMixin:
    def reset(self):
        _APP_LABELS.clear()
        _URL_NAMES.clear()

    def setUp(self) -> None:
        super().setUp()
        self.reset()

    def tearDown(self) -> None:
        super().tearDown()
        self.reset()


class DataTypesTestCase(ClearDataTypesInfoMixin, SimpleTestCase):

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
        with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs, self.assertLogs(
            'django.request', level=logging.WARNING
        ):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        assert logs.output == [
            "WARNING:bx_django_utils.admin_extra_views.base_view:"
            "User (pk:None) did not pass 'only_staff_user' for 'DemoView1'"
        ]

        # Non-staff users can also not access:
        self.client.force_login(self.non_staff_user)
        with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs, self.assertLogs(
            'django.request', level=logging.WARNING
        ):
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
        assert_html_response_snapshot(
            response,
            query_selector='#content-main',
            validate=False,
            name_suffix=get_django_name_suffix(),
        )

        # Pseudo apps should not have a "app index" view link,
        # because there is no url/view that will handle this!
        self.assert_parts_not_in_html(
            response,
            parts=(
                '"/admin/pseudo-app-1/"',
                '"/admin/pseudo-app-2/"',
            ),
        )

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
        with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs, self.assertLogs(
            'django.request', level=logging.WARNING
        ):
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

    def test_admin_app_page(self):
        # Test for: https://github.com/boxine/bx_django_utils/issues/125
        # TypeError: ExtraViewAdminSite.get_app_list() takes 2 positional arguments but 3 were given
        self.client.force_login(self.superuser)
        response = self.client.get('/admin/auth/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTemplateUsed(response, 'admin/app_index.html')
        self.assert_html_parts(response, parts=('<h1>Authentication and Authorization administration</h1>',))
        self.assert_parts_not_in_html(response, parts=('pseudo', 'Pseudo App'))

        # Pseudo apps has no "app index" view:
        with NoLogs(logger_name='django.request'):
            response = self.client.get('/admin/pseudo-app-1/')
        self.assertEqual(response.status_code, 404, response.content)


class AdminExtraViewSimpleTestCase(SimpleTestCase):
    def test_reverse_admin_extra_view(self):
        url = reverse_admin_extra_view(DemoView2)
        self.assertEqual(url, '/admin/pseudo-app-1/demo-view-2/')

    def test_redirect_view(self):
        redirect_view = Redirect2AdminExtraView.as_view(admin_view=DemoView2)

        dummy_request = RequestFactory().request()
        response = redirect_view(request=dummy_request)
        self.assertRedirects(
            response, expected_url='/admin/pseudo-app-1/demo-view-2/', fetch_redirect_response=False
        )

    def test_redirect_view_via_urls(self):
        response = self.client.get('/old_demo_3/')
        self.assertRedirects(
            response, expected_url='/admin/pseudo-app-2/demo-view-3/', fetch_redirect_response=False
        )


class ManageCommandTestCase(TestCase):
    def test_admin_extra_views_command(self):
        capture_stdout = io.StringIO()
        capture_stderr = io.StringIO()
        call_command(admin_extra_views.Command(), stdout=capture_stdout, stderr=capture_stderr)
        stdout_output = capture_stdout.getvalue()
        stderr_output = capture_stderr.getvalue()

        self.assertIn('Pseudo App 1', stdout_output)
        self.assertIn('Demo View 1', stdout_output)
        self.assertIn('/admin/pseudo-app-1/demo-view-1/', stdout_output)
        self.assertEqual(stderr_output, '')


class ChecksTestCase(ClearDataTypesInfoMixin, TestCase):
    def setUp(self):
        self._old_pseudo_apps = extra_view_registry.pseudo_apps.copy()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        extra_view_registry.pseudo_apps = self._old_pseudo_apps

    def test_no_errors(self):
        errors = admin_extra_views_check(app_configs=None)
        self.assertEqual(errors, [])

    def test_custom_admin_site(self):
        class CustomAdminSite(ExtraViewAdminSite):
            pass

        @register_admin_view(
            pseudo_app=PseudoApp(
                meta=AdminExtraMeta(name='Foo'),
                admin_site=CustomAdminSite(),
            )
        )
        class TestView(AdminExtraViewMixin, View):
            meta = AdminExtraMeta(name='Bar')

        errors = admin_extra_views_check(app_configs=None)

        # We should only get the "URL reverse error" because CustomAdminSite is not in urls.py ;)
        self.assertEqual(len(errors), 1)
        reverse_error = errors[0]
        self.assertEqual(reverse_error.id, 'admin_extra_views.E001')

    def test_wrong_admin_site(self):
        @register_admin_view(
            pseudo_app=PseudoApp(
                meta=AdminExtraMeta(name='Foo'),
                admin_site=AdminSite(),
            )
        )
        class TestView(AdminExtraViewMixin, View):
            meta = AdminExtraMeta(name='Bar')

        errors = admin_extra_views_check(app_configs=None)
        self.assertEqual(len(errors), 2)
        reverse_error = errors[0]
        self.assertEqual(reverse_error.id, 'admin_extra_views.E001')
        self.assertEqual(reverse_error.msg, "Admin extra views URL reverse error with 'TestView'")

        admin_class_error = errors[1]
        self.assertEqual(admin_class_error.id, 'admin_extra_views.E002')
        self.assertEqual(
            admin_class_error.msg,
            "Pseudo app 'Foo' error: Admin site 'AdminSite'"
            " is not a instance of ExtraViewAdminSite!",
        )
