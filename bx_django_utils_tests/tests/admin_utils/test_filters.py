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
                '<summary>By blank_field set</summary>',
                '<li><a href="?blank_field=all">All</a></li>',
                '<li class="selected"><a href="?">Yes</a></li>',  # Yes is default!
                '<li><a href="?blank_field=no">No</a></li>',
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
                '<summary>By blank_field set</summary>',
                '<li><a href="?blank_field=all">All</a></li>',
                '<li><a href="?">Yes</a></li>',  # Yes is default!
                '<li class="selected"><a href="?blank_field=no">No</a></li>',
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
                '<summary>By blank_field set</summary>',
                '<li class="selected"><a href="?blank_field=all">All</a></li>',
                '<li><a href="?">Yes</a></li>',  # Yes is default!
                '<li><a href="?blank_field=no">No</a></li>',
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


class ExistingCountedListFilterTestCase(HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.superuser = make_test_user(is_superuser=True)

        baker.make(
            CreateOrUpdateTestModel,
            pk=1,
            name='<foo> / <bar>',
            slug='foo-bar',
            blank_field='a value',
        )
        baker.make(
            CreateOrUpdateTestModel,
            pk=2,
            name='Foo',
            slug='foo',
            blank_field='a value',
        )
        baker.make(
            CreateOrUpdateTestModel,
            pk=3,
            name='Foo',
            slug='foo2',
            blank_field='a value',
        )

    def _get_changelist_items(self, response):
        results = response.context['results']
        items = [items[-1] for items in results]
        return items

    def test_admin(self):
        self.client.force_login(self.superuser)

        response = self.client.get('/admin/test_app/createorupdatetestmodel/')
        self.assert_html_parts(
            response,
            parts=(
                '<summary>By name</summary>',
                (
                    '<li>'
                    '<a href="?name=%253Cfoo%253E%2B%252F%2B%253Cbar%253E">'
                    '&lt;foo&gt; / &lt;bar&gt; (1)</a>'
                    '</li>'
                ),
                '<li><a href="?name=Foo">Foo (2)</a></li>',
            ),
        )
        items = self._get_changelist_items(response)
        self.assertEqual(
            items,
            [
                (
                    '<td class="field-slug">'
                    '<a href="/admin/test_app/createorupdatetestmodel/3/change/">'
                    'foo2</a></td>'
                ),
                (
                    '<td class="field-slug">'
                    '<a href="/admin/test_app/createorupdatetestmodel/2/change/">'
                    'foo</a></td>'
                ),
                (
                    '<td class="field-slug">'
                    '<a href="/admin/test_app/createorupdatetestmodel/1/change/">'
                    'foo-bar</a></td>'
                ),
            ],
        )

        ###################################################################################

        response = self.client.get(
            '/admin/test_app/createorupdatetestmodel/?name=%253Cfoo%253E%2B%252F%2B%253Cbar%253E'
        )
        self.assert_html_parts(
            response,
            parts=(
                '<summary>By name</summary>',
                (
                    '<li class="selected">'
                    '<a href="?name=%253Cfoo%253E%2B%252F%2B%253Cbar%253E">'
                    '&lt;foo&gt; / &lt;bar&gt; (1)</a>'
                    '</li>'
                ),
                '<li><a href="?name=Foo">Foo (2)</a></li>',
            ),
        )
        items = self._get_changelist_items(response)
        self.assertEqual(
            items,
            [
                '<td class="field-slug">'
                '<a href="/admin/test_app/createorupdatetestmodel/1/change/'
                '?_changelist_filters=name%3D%25253Cfoo%25253E%252B%25252F%252B%25253Cbar%25253E">'
                'foo-bar</a></td>'
            ],
        )
