import unittest
from unittest import TestCase

import django

from bx_django_utils_tests.test_app.management.commands.update_readme import (
    auto_doc_in_readme,
)


class Readme(TestCase):
    @unittest.skipUnless(
        condition=django.VERSION >= (6, 0),
        reason='Use Django 6.0+ DocStrings',
    )
    def test_auto_doc_in_readme(self):
        auto_doc_in_readme()
