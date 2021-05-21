from django.test import SimpleTestCase

from bx_django_utils.compat import removeprefix, removesuffix


class CompatTest(SimpleTestCase):
    def test_removeprefix(self):
        assert removeprefix('fooobar', 'fooo') == 'bar'
        assert removeprefix('fooobar', 'bar') == 'fooobar'
        assert removeprefix('xyz', 'xyz') == ''

    def test_removesuffix(self):
        assert removesuffix('fooobar', 'bar') == 'fooo'
        assert removesuffix('fooobar', 'fooo') == 'fooobar'
        assert removesuffix('xyz', 'xyz') == ''
