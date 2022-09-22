import sys
from pathlib import Path

import pytest
from bx_py_utils.auto_doc import FnmatchExclude, assert_readme

import bx_django_utils


PY39PLUS = (3, 9) <= sys.version_info


# pdoc is not compatible with Python 3.6 and
# we get different results between 3.8 and 3.9,
# so update the README only with 3.9 and newer for now
@pytest.mark.skipif(not PY39PLUS, reason='requires Python v3.9 or newer')
def test_auto_doc_in_readme():
    root_path = Path(bx_django_utils.__file__).parent.parent
    readme_path = root_path / 'README.md'

    assert_readme(
        readme_path=readme_path,
        modules=['bx_django_utils'],
        exclude_func=FnmatchExclude('*/migrations/*'),
        start_marker_line='[comment]: <> (✂✂✂ auto generated start ✂✂✂)',
        end_marker_line='[comment]: <> (✂✂✂ auto generated end ✂✂✂)',
        start_level=2,
        link_template='https://github.com/boxine/bx_django_utils/blob/master/{path}#L{start}-L{end}'
    )
