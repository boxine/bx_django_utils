"""
    Helper to publish this Project to PyPi
"""

from pathlib import Path

from bx_py_utils.path import assert_is_file
from cli_base.cli_tools.subprocess_utils import verbose_check_call
from manageprojects.utilities.publish import publish_package

import bx_django_utils


def publish():
    """
    Publish to PyPi
    Call this via:
        $ .venv/bin/publish
    """
    package_path = Path(bx_django_utils.__file__).parent.parent
    assert_is_file(package_path / 'pyproject.toml')

    verbose_check_call('make', 'test')  # don't publish if tests fail
    verbose_check_call('make', 'fix-code-style')  # don't publish if code style wrong

    publish_package(
        module=bx_django_utils,
        package_path=package_path,
    )


if __name__ == '__main__':
    publish()
