import os
import unittest
from pathlib import Path

import bx_django_utils


# Hacky way to display more "assert"-Context in failing tests:
unittest.util._MAX_LENGTH = os.environ.get('UNITTEST_MAX_LENGTH', 200)


PACKAGE_ROOT = Path(bx_django_utils.__file__).parent.parent
