from pathlib import Path

from bx_py_utils.auto_doc import FnmatchExclude, assert_readme
from django.core.management import BaseCommand

import bx_django_utils


README_FILENAME = 'README.md'


def auto_doc_in_readme():
    root_path = Path(bx_django_utils.__file__).parent.parent
    readme_path = root_path / README_FILENAME

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


class Command(BaseCommand):
    help = 'Update README.md (will be also done in tests)'

    def handle(self, *args, **options):
        auto_doc_in_readme()
        self.stdout.write(f'{README_FILENAME} updated')
