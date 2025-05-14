from pathlib import Path
from unittest import TestCase

from bx_py_utils.doc_write.api import GeneratedInfo, generate
from bx_py_utils.path import assert_is_file

import bx_django_utils


class DocuWriteApiTestCase(TestCase):
    def test_up2date_docs(self):
        """DocWrite: README.md # docs
        We update the documentation files with the `bx_py_utils.doc_write` module.
        More info:
        https://github.com/boxine/bx_py_utils/tree/master/bx_py_utils/doc_write
        """
        base_path = Path(bx_django_utils.__file__).parent.parent
        assert_is_file(base_path / 'pyproject.toml')

        info: GeneratedInfo = generate(base_path=base_path)
        self.assertGreaterEqual(len(info.paths), 1)
        self.assertEqual(info.update_count, 0, 'No files should be updated, commit the changes')
        self.assertEqual(info.remove_count, 0, 'No files should be removed, commit the changes')
