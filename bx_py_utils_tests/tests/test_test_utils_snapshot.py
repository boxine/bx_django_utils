import pathlib
import tempfile

import pytest

from bx_py_utils.test_utils.snapshot import assert_snapshot, assert_text_snapshot


def test_assert_snapshot():
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(FileNotFoundError) as excinfo:
            assert_snapshot(tmp_dir, 'snap', [{'foo': 42, 'bär': 5}])
        assert 'No such file or directory' in str(excinfo.value)
        assert tmp_dir in str(excinfo.value)
        assert 'snap.json' in str(excinfo.value)

        assert_snapshot(tmp_dir, 'snap', [{'foo': 42, 'bär': 5}])

        with pytest.raises(AssertionError) as exc_info:
            assert_snapshot(tmp_dir, 'snap', [{'foo': 42, 'bär': 23}])
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


def test_assert_text_snapshot():
    with tempfile.TemporaryDirectory() as tmp_dir:
        TEXT = 'this is\nmultiline "text"'
        with pytest.raises(FileNotFoundError):
            assert_text_snapshot(tmp_dir, 'text', TEXT)
        written_text = (pathlib.Path(tmp_dir) / 'text.snapshot.txt').read_text()
        assert written_text == TEXT

        assert_text_snapshot(tmp_dir, 'text', TEXT)

        with pytest.raises(AssertionError) as exc_info:
            assert_text_snapshot(tmp_dir, 'text', 'changed')
        written_text = (pathlib.Path(tmp_dir) / 'text.snapshot.txt').read_text()
        assert written_text == 'changed'
        assert exc_info.value.args[0] == (
            'Text not equal:\n'
            '- changed\n'
            '+ this is\n'
            '+ multiline "text"'
        )

        assert_text_snapshot(tmp_dir, 'text', 'changed')

        with pytest.raises(FileNotFoundError):
            assert_text_snapshot(tmp_dir, 'text', TEXT, extension='.test2')
        written_text = (pathlib.Path(tmp_dir) / 'text.snapshot.test2').read_text()
        assert written_text == TEXT
