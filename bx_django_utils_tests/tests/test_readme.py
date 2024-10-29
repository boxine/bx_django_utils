from pathlib import Path
from unittest import TestCase

from bx_py_utils.auto_doc import FnmatchExclude, assert_readme

import bx_django_utils


class Readme(TestCase):
    def test_auto_doc_in_readme(self):
        root_path = Path(bx_django_utils.__file__).parent.parent
        readme_path = root_path / 'README.md'

        assert_readme(
            readme_path=readme_path,
            modules=['bx_django_utils'],
            exclude_func=FnmatchExclude('*/migrations/*'),
            exclude_prefixes=('DocWrite:', '[no-doc]'),
            start_marker_line='[comment]: <> (✂✂✂ auto generated start ✂✂✂)',
            end_marker_line='[comment]: <> (✂✂✂ auto generated end ✂✂✂)',
            start_level=2,
            link_template='https://github.com/boxine/bx_django_utils/blob/master/{path}#L{start}-L{end}',
        )
