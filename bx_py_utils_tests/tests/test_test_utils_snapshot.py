import pathlib
import tempfile

import pytest

from bx_py_utils.test_utils.snapshot import assert_snapshot


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
