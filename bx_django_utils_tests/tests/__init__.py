import os
import unittest


# Hacky way to display more "assert"-Context in failing tests:
unittest.util._MAX_LENGTH = os.environ.get('UNITTEST_MAX_LENGTH', 200)
