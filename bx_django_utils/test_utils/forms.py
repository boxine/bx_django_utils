from django.http import HttpResponse
from lxml import etree


def _sorted_join_repr(iterable):  # TODO: Move to bx_py_utils?
    """
    >>> _sorted_join_repr(['baz', 'foo', 'bar'])
    "'bar', 'baz', 'foo'"
    """
    return ', '.join(repr(item) for item in sorted(iterable))


class AssertFormFields:
    """
    Helper to check the existing form fields.
    e.g.:
        response = self.client.get('/foo/bar/form.html')
        assert_form_fields = AssertFormFields(response)
        self.assertGreaterEqual(len(assert_form_fields), 30) # Min. 30 fields?
        assert_form_fields.assert_field_names_not_exists(
            field_names={'internal', 'foo', 'bar'}
        )
        assert_form_fields.assert_field_names_exists(
            field_names={'normal_field1', 'normal_field2'}
        )
        assert_snapshot(got=assert_form_fields.data)
    """

    def __init__(
        self,
        response: HttpResponse,
        xpath_prefix='//div[@id="content"]',  # Collect fields only in this page part
        xpath_filter='[not(@type="hidden")]',  # Ignore hidden fields as default
    ):

        parser = etree.HTMLParser()
        tree = etree.fromstring(response.content, parser=parser)
        form_fields = tree.xpath(
            f'{xpath_prefix}//form//*[self::input or self::textarea or self::select]{xpath_filter}'
        )

        # Collect only the attributes of the <input> field:
        self.data = []
        for element in form_fields:
            attrib = dict(element.attrib)  # Make if JSON serializable for snapshot test
            self.data.append(attrib)

        # The main purpose here is to test which fields are available,
        # not how they are sorted on the website.
        #
        # Sort them for snapshot test:
        self.data.sort(key=lambda x: (x.get('name', ''), x.get('id', '')))

    def get_all_field_names(self) -> set:
        """
        :return: All existing field names (NOTE: Ignores fields without name!)
        """
        all_field_names = {attrib['name'] for attrib in self.data if attrib.get('name')}
        return all_field_names

    def assert_field_names_exists(self, field_names) -> None:
        """
        Check that form field exists by name
        """
        expected_field_names = set(field_names)
        existing_field_names = self.get_all_field_names()
        missing_field_names = expected_field_names - existing_field_names
        assert not missing_field_names, (
            f'Fields: {_sorted_join_repr(missing_field_names)}'
            f' are not present in: {_sorted_join_repr(existing_field_names)}'
        )

    def assert_field_names_not_exists(self, field_names) -> None:
        """
        Check that form fields doesn't exist by name
        """
        should_not_present = set(field_names)
        existing_field_names = self.get_all_field_names()
        occurring_names = should_not_present & existing_field_names
        assert not occurring_names, (
            f'These fields should not occur,'
            f' but are present: {_sorted_join_repr(occurring_names)}'
        )

    def __len__(self):
        return len(self.data)
