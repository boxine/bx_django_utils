from bx_py_utils.test_utils.unittest_utils import BaseDocTests

import bx_django_utils
import bx_django_utils_tests


class DocTests(BaseDocTests):
    def test_doctests(self):
        self.run_doctests(
            modules=(bx_django_utils, bx_django_utils_tests),
        )
