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

        with pytest.raises(AssertionError):
            assert_snapshot(tmp_dir, 'snap', [{'foo': 42, 'bär': 23}])


def test_assert_text_snapshot():
    with tempfile.TemporaryDirectory() as tmp_dir:
        TEXT = 'this is\nmultiline "text"'
        with pytest.raises(FileNotFoundError) as excinfo:
            assert_text_snapshot(tmp_dir, 'text', TEXT)
        written_text = (pathlib.Path(tmp_dir) / 'text.snapshot.txt').read_text()
        assert written_text == TEXT

        assert_text_snapshot(tmp_dir, 'text', TEXT)

        with pytest.raises(AssertionError):
            assert_text_snapshot(tmp_dir, 'text', 'changed')
        written_text = (pathlib.Path(tmp_dir) / 'text.snapshot.txt').read_text()
        assert written_text == 'changed'

        assert_text_snapshot(tmp_dir, 'text', 'changed')

        with pytest.raises(FileNotFoundError) as excinfo:
            assert_text_snapshot(tmp_dir, 'text', TEXT, extension='.test2')
        written_text = (pathlib.Path(tmp_dir) / 'text.snapshot.test2').read_text()
        assert written_text == TEXT
