from django.test import TestCase
from model_bakery import baker

from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from bx_django_utils.test_utils.users import make_test_user
from bx_django_utils_tests.test_app.models import CreateOrUpdateTestModel


class NotAllSimpleListFilterTestCase(HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.superuser = make_test_user(is_superuser=True)

        baker.make(
            CreateOrUpdateTestModel,
            pk=1,
            name='with empty blank field',
            slug='empty',
            blank_field='',
        )
        baker.make(
            CreateOrUpdateTestModel,
            pk=2,
            name='with filled blank field',
            slug='filled',
            blank_field='a value',
        )

    def _get_changelist_items(self, response):
        results = response.context['results']
        items = [items[-1] for items in results]
        return items

    def test_admin(self):
        self.client.force_login(self.superuser)

        ###################################################################################
        # without filter -> default

        response = self.client.get('/admin/test_app/createorupdatetestmodel/')
        self.assert_html_parts(
            response,
            parts=(
                '<h3>By blank_field set</h3>',
                '<li><a href="?blank_field=all" title="All">All</a></li>',
                '<li class="selected"><a href="?" title="Yes">Yes</a></li>',  # Yes is default!
                '<li><a href="?blank_field=no" title="No">No</a></li>',
            ),
        )
        # Only "filled" item?
        items = self._get_changelist_items(response)
        self.assertEqual(
            items,
            [
                '<td class="field-slug">'
                '<a href="/admin/test_app/createorupdatetestmodel/2/change/">filled</a></td>'
            ],
        )

        ###################################################################################
        # only blank fields

        response = self.client.get('/admin/test_app/createorupdatetestmodel/?blank_field=no')
        self.assert_html_parts(
            response,
            parts=(
                '<h3>By blank_field set</h3>',
                '<li><a href="?blank_field=all" title="All">All</a></li>',
                '<li><a href="?" title="Yes">Yes</a></li>',
                '<li class="selected"><a href="?blank_field=no" title="No">No</a></li>',
            ),
        )
        # Only "empty" item?
        items = self._get_changelist_items(response)
        self.assertEqual(
            items,
            [
                '<td class="field-slug">'
                '<a href="/admin/test_app/createorupdatetestmodel/1/change/'
                '?_changelist_filters=blank_field%3Dno">empty</a></td>'
            ],
        )

        ###################################################################################
        # all entries

        response = self.client.get('/admin/test_app/createorupdatetestmodel/?blank_field=all')
        self.assert_html_parts(
            response,
            parts=(
                '<h3>By blank_field set</h3>',
                '<li class="selected"><a href="?blank_field=all" title="All">All</a></li>',
                '<li><a href="?" title="Yes">Yes</a></li>',
                '<li><a href="?blank_field=no" title="No">No</a></li>',
            ),
        )
        # Both: "filled" and "empty" items?
        items = self._get_changelist_items(response)
        self.assertEqual(
            items,
            [
                '<td class="field-slug"><a href="/admin/test_app/createorupdatetestmodel/2/change/'
                '?_changelist_filters=blank_field%3Dall">filled</a></td>',
                '<td class="field-slug"><a href="/admin/test_app/createorupdatetestmodel/1/change/'
                '?_changelist_filters=blank_field%3Dall">empty</a></td>',
            ],
        )
