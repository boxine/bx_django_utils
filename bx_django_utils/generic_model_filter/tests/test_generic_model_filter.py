from django.contrib.admin.models import ACTION_FLAG_CHOICES, LogEntry
from django.contrib.auth.models import User
from django.test import TestCase
from model_bakery import baker

from bx_django_utils.admin_extra_views.utils import reverse_admin_extra_view
from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from bx_django_utils_tests.test_app.admin_views import GenericModelFilterAdminExtraView


class GenericModelFilterTestCase(HtmlAssertionMixin, TestCase):
    """[no-doc]"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.super_user = User.objects.create_superuser(username='foobar')

    def test_basics(self):
        url = reverse_admin_extra_view(GenericModelFilterAdminExtraView)
        self.assertEqual(url, '/admin/generic-model-filter/generic-filter/')

        for action_choice in ACTION_FLAG_CHOICES:
            action = action_choice[0]
            for object_id in (None, 'foo', 'foo', 'bar'):
                baker.make(LogEntry, object_id=object_id, action_flag=action)

        self.client.force_login(self.super_user)

        #########################################################################
        # Step 1: selected model to be searched

        response = self.client.get('/admin/generic-model-filter/generic-filter/')
        self.assertTemplateUsed(response, template_name='generic_model_filter.html')
        self.assert_html_parts(
            response,
            parts=(
                '<h1>Generic model item filter</h1>',
                '<h2>Step 1: selected model to be searched</h2>',
                '<label for="id_model_name">Model Name:</label>',
                '<option value="auth.User">Authentication and Authorization | user</option>',
            ),
        )

        response = self.client.post(
            path='/admin/generic-model-filter/generic-filter/', data={'model_name': 'admin.LogEntry'}
        )
        self.assertRedirects(
            response,
            expected_url='/admin/generic-model-filter/generic-filter/?model_name=admin.LogEntry',
            fetch_redirect_response=False,
        )

        #########################################################################
        # Step 2: selected fields to be searched on the selected model

        response = self.client.get('/admin/generic-model-filter/generic-filter/?model_name=admin.LogEntry')
        self.assert_html_parts(
            response,
            parts=(
                '<h1>Generic model item filter</h1>',
                '<h2>Step 2: selected fields to be searched on the selected model</h2>',
                '<label for="id_field_names">Fields:</label>',
                '<option value="action_flag">action flag</option>',
            ),
        )

        response = self.client.post(
            path='/admin/generic-model-filter/generic-filter/?model_name=admin.LogEntry',
            data={'field_names': ['object_id', 'action_flag']},
        )
        self.assertRedirects(
            response,
            expected_url=(
                '/admin/generic-model-filter/generic-filter/'
                '?model_name=admin.LogEntry'
                '&field_names=object_id'
                '&field_names=action_flag'
            ),
            fetch_redirect_response=False,
        )

        #########################################################################
        # Step 3: The field values used to filter the model

        response = self.client.get(
            path=(
                '/admin/generic-model-filter/generic-filter/'
                '?model_name=admin.LogEntry'
                '&field_names=object_id'
                '&field_names=action_flag'
            )
        )
        self.assert_html_parts(
            response,
            parts=(
                '<h1>Generic model item filter</h1>',
                '<h2>Step 3: The field values used to filter the model</h2>',
                '<label for="id_object_id">Object id:</label>',
                '<option value="1">Addition</option>',
                '<option value="2">Change</option>',
            ),
        )

        self.assertNotIn('generic_model_filter', self.client.session)

        response = self.client.post(
            path=(
                '/admin/generic-model-filter/generic-filter/'
                '?model_name=admin.LogEntry'
                '&field_names=object_id'
                '&field_names=action_flag'
            ),
            data={
                'object_id': 'foo',
                'is_null_check_action_flag': '1',
            },
        )
        self.assertRedirects(
            response,
            expected_url=(
                '/admin/generic-model-filter/generic-filter/'
                '?model_name=admin.LogEntry'
                '&field_names=object_id'
                '&field_names=action_flag'
            ),
            fetch_redirect_response=False,
        )
        self.assertIn('generic_model_filter', self.client.session)
        data = self.client.session['generic_model_filter']
        self.assertEqual(
            data,
            {'object_id': 'foo', 'action_flag': '', 'is_null_check_object_id': '', 'is_null_check_action_flag': '1'},
        )

        #########################################################################
        # Search result

        response = self.client.get(
            path=(
                '/admin/generic-model-filter/generic-filter/'
                '?model_name=admin.LogEntry'
                '&field_names=object_id'
                '&field_names=action_flag'
            )
        )
        self.assert_html_parts(
            response,
            parts=(
                '<h1>Generic model item filter</h1>',
                '<h2>Found 6 entries (total: 12)</h2>',
                '<span class="current">Page 1 of 1.</span>',
            ),
        )
