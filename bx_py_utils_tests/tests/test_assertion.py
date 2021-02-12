from django.test import SimpleTestCase

from bx_py_utils.test_utils.assertion import assert_equal


class AssertionTestCase(SimpleTestCase):
    def test_assert_equal(self):
        assert_equal(1, 1)
        assert_equal('a', 'a')
        x = object
        assert_equal(x, x)

        with self.assertRaisesMessage(AssertionError, 'Objects are not equal:\n- 1\n+ 2'):
            assert_equal(1, 2)

        msg = (
            'Objects are not equal:\n'
            '  [\n'
            '      {\n'
            '          "1": {\n'
            '-             "2": "two"\n'
            '?                   ^^^\n'
            '\n'
            '+             "2": "XXX"\n'
            '?                   ^^^\n'
            '\n'
            '          }\n'
            '      }\n'
            '  ]'
        )
        with self.assertRaisesMessage(AssertionError, msg):
            assert_equal(
                [{1: {2: 'two'}}],
                [{1: {2: 'XXX'}}]
            )
