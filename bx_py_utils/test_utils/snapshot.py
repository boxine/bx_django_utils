import json
import pathlib
import re
from typing import Union


def _write_json(obj, snapshot_file):
    with snapshot_file.open('w') as snapshot_handle:
        json.dump(obj, snapshot_handle, ensure_ascii=False, indent=4, sort_keys=True)


def assert_text_snapshot(root_dir: Union[pathlib.Path, str], snapshot_name: str, got: str):
    assert re.match(r'^[-_.a-zA-Z0-9]+$', snapshot_name), f'Invalid snapshot name {snapshot_name}'
    assert isinstance(got, str)

    snapshot_file = pathlib.Path(root_dir) / f'{snapshot_name}.snapshot.txt'
    try:
        expected = snapshot_file.read_text()
    except (FileNotFoundError, IOError, OSError):
        snapshot_file.write_text(got)
        raise

    if got != expected:
        snapshot_file.write_text(got)

        assert got == expected


def assert_snapshot(root_dir: Union[pathlib.Path, str], snapshot_name: str, got: Union[dict, list]):
    assert re.match(r'^[-_.a-zA-Z0-9]+$', snapshot_name), f'Invalid snapshot name {snapshot_name}'
    assert isinstance(got, (dict, list))

    snapshot_file = pathlib.Path(root_dir) / f'{snapshot_name}.json'
    try:
        with snapshot_file.open('r') as snapshot_handle:
            expected = json.load(snapshot_handle)
    except (ValueError, IOError, FileNotFoundError, OSError):
        _write_json(got, snapshot_file)
        raise

    if got != expected:
        _write_json(got, snapshot_file)

        assert got == expected
