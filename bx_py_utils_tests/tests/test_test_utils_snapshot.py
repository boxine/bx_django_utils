import pathlib
import tempfile

import pytest

from bx_py_utils.test_utils.assertion import pformat_ndiff, text_ndiff
from bx_py_utils.test_utils.snapshot import assert_snapshot, assert_text_snapshot


def test_assert_snapshot():
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(FileNotFoundError) as excinfo:
            assert_snapshot(tmp_dir, 'snap', [{'foo': 42, 'bär': 5}])
        assert 'No such file or directory' in str(excinfo.value)
        assert tmp_dir in str(excinfo.value)
        assert 'snap.json' in str(excinfo.value)

        assert_snapshot(tmp_dir, 'snap', [{'foo': 42, 'bär': 5}])

        # ndiff error message:

        with pytest.raises(AssertionError) as exc_info:
            assert_snapshot(tmp_dir, 'snap', [{'foo': 42, 'bär': 23}], diff_func=pformat_ndiff)
        assert exc_info.value.args[0] == (
            'Objects are not equal:\n'
            '  [\n'
            '      {\n'
            '-         "bär": 23,\n'
            '?                ^^\n'
            '\n'
            '+         "bär": 5,\n'
            '?                ^\n'
            '\n'
            '          "foo": 42\n'
            '      }\n'
            '  ]'
        )

        # unified diff error message:

        with pytest.raises(AssertionError) as exc_info:
            assert_snapshot(tmp_dir, 'snap', [{'foo': 42, 'bär': 123}])
        assert exc_info.value.args[0] == (
            'Objects are not equal:\n'
            '--- got\n'
            '\n'
            '+++ expected\n'
            '\n'
            '@@ -1,6 +1,6 @@\n'
            '\n'
            ' [\n'
            '     {\n'
            '-        "bär": 123,\n'
            '+        "bär": 23,\n'
            '         "foo": 42\n'
            '     }\n'
            ' ]'
        )

def test_assert_text_snapshot():
    with tempfile.TemporaryDirectory() as tmp_dir:
        TEXT = 'this is\nmultiline "text"\none\ntwo\nthree\nfour'
        with pytest.raises(FileNotFoundError):
            assert_text_snapshot(tmp_dir, 'text', TEXT)
        written_text = (pathlib.Path(tmp_dir) / 'text.snapshot.txt').read_text()
        assert written_text == TEXT

        assert_text_snapshot(tmp_dir, 'text', TEXT)

        # Error message with ndiff:

        with pytest.raises(AssertionError) as exc_info:
            assert_text_snapshot(
                tmp_dir, 'text', 'this is:\nmultiline "text"\none\ntwo\nthree\nfour',
                diff_func=text_ndiff
            )
        written_text = (pathlib.Path(tmp_dir) / 'text.snapshot.txt').read_text()
        assert written_text == 'this is:\nmultiline "text"\none\ntwo\nthree\nfour'
        print(repr(exc_info.value.args[0]))
        assert exc_info.value.args[0] == (
            'Text not equal:\n'
            '- this is:\n'
            '?        -\n'
            '\n'
            '+ this is\n'
            '  multiline "text"\n'
            '  one\n'
            '  two\n'
            '  three\n'
            '  four'
        )

        # Error message with unified diff:

        with pytest.raises(AssertionError) as exc_info:
            assert_text_snapshot(
                tmp_dir, 'text',
                'This is:\nmultiline "text"\none\ntwo\nthree\nfour',
            )
        print(repr(exc_info.value.args[0]))
        assert exc_info.value.args[0] == (
            'Text not equal:\n'
            '--- got\n'
            '\n'
            '+++ expected\n'
            '\n'
            '@@ -1,4 +1,4 @@\n'
            '\n'
            '-This is:\n'
            '+this is:\n'
            ' multiline "text"\n'
            ' one\n'
            ' two'
        )

        assert_text_snapshot(tmp_dir, 'text', 'This is:\nmultiline "text"\none\ntwo\nthree\nfour')

        with pytest.raises(FileNotFoundError):
            assert_text_snapshot(tmp_dir, 'text', TEXT, extension='.test2')
        written_text = (pathlib.Path(tmp_dir) / 'text.snapshot.test2').read_text()
        assert written_text == TEXT
