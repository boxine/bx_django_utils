from unittest import TestCase

from bx_django_utils_tests.test_app.management.commands.update_readme import (
    auto_doc_in_readme,
)


class Readme(TestCase):
    def test_auto_doc_in_readme(self):
        auto_doc_in_readme()
