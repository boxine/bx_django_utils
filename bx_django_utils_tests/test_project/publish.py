"""
    Helper to publish this Project to PyPi
"""

from pathlib import Path

from manageprojects.utilities.publish import publish_package
from manageprojects.utilities.subprocess_utils import verbose_check_call

import bx_django_utils


PACKAGE_ROOT = Path(bx_django_utils.__file__).parent.parent


def publish():
    """
    Publish to PyPi
    Call this via:
        $ poetry run publish
    """
    verbose_check_call('make', 'test')  # don't publish if tests fail
    verbose_check_call('make', 'fix-code-style')  # don't publish if code style wrong

    publish_package(
        module=bx_django_utils,
        package_path=PACKAGE_ROOT,
    )
