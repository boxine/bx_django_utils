import uuid
from unittest import TestCase

from bx_py_utils.test_utils.datetime import parse_dt

from bx_django_utils.json_utils import make_json_serializable, to_json


class TestObject:
    __test__ = False

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return f'<TestObject {self.text}>'


def convert_func_example(obj):
    assert isinstance(obj, TestObject)
    return obj.text


class JsonUtilsTestCase(TestCase):
    def test_make_json_serializable(self):
        assert make_json_serializable([
            1, [2, 3], {4: 5, 6: TestObject('foo'), 7: TestObject('bar')}
        ]) == [
            1, [2, 3], {4: 5, 6: '<TestObject foo>', 7: '<TestObject bar>'}
        ]

        assert make_json_serializable(
            [1, [2, 3], {4: 5, 6: TestObject('foo'), 7: TestObject('bar')}],
            convert_func=convert_func_example
        ) == [
            1, [2, 3], {4: 5, 6: 'foo', 7: 'bar'}
        ]

    def test_to_json(self):
        assert to_json([1, 2, 3]) == '[1, 2, 3]'

        assert to_json([
            uuid.UUID('00000000-1111-0000-0000-000000000001'),
            parse_dt('2000-01-01T01:01:01+0100')
        ]) == (
            '["00000000-1111-0000-0000-000000000001", "2000-01-01T01:01:01+01:00"]'
        )

    def test_to_json_convert_func(self):
        assert to_json([TestObject('foo'), TestObject('bar')]) == (
            '["<TestObject foo>", "<TestObject bar>"]'
        )

        assert to_json(
            [TestObject('foo'), TestObject('bar')],
            convert_func=convert_func_example
        ) == '["foo", "bar"]'
