import functools
from pathlib import Path
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand


DEFAULT_VERSION_FILE_NAME = 'VERSION'


@functools.lru_cache
def get_version(raise_error=False, base_dir: Path | None = None, file_name: str = DEFAULT_VERSION_FILE_NAME):
    """
    Get version of this application. First try to read it from file, then determine from git.
    """
    if not base_dir:
        base_dir = Path(settings.BASE_DIR)
    version_file = base_dir / file_name
    try:
        version_text = version_file.read_text()
        return version_text.strip()
    except OSError:
        pass

    return determine_version(raise_error=raise_error, base_dir=version_file.parent)


def determine_version(raise_error=False, base_dir: Path | None = None):
    if not base_dir:
        base_dir = settings.BASE_DIR
    return _git_version(base_dir=base_dir, raise_error=raise_error)


def _git_version(base_dir: Path, raise_error=False):
    try:
        tags_str = subprocess.check_output(['git', 'tag', '--points-at', 'HEAD'], cwd=base_dir).decode('utf-8').strip()
        sha = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=base_dir).decode('utf-8').strip()

        names = tags_str.split() + [sha]
        res = '/'.join(names)

        status = subprocess.check_output(['git', 'status', '--untracked-files=no', '--porcelain'], cwd=base_dir).decode(
            'utf-8'
        )

        # Ignore changes in ebextensions (gets rewritten automatically)
        status_lines = [line for line in status.split('\n') if line and not line.startswith(' M .ebextensions/')]
        if status_lines:
            res += '+changes'
        return res
    except (FileNotFoundError, subprocess.CalledProcessError):
        if raise_error:
            raise
        return 'unknown'


class DetermineVersionCommand(BaseCommand):
    """ Write application version determined from git as a command """
    help = 'Determine version of this application from git'

    def add_arguments(self, parser):
        parser.add_argument(
            '-g',
            '--get-from-file',
            action='store_true',
            help='Instead of determining the version from scratch, read it from file if possible',
        )
        parser.add_argument('-r', '--raise-error', action='store_true', help='Fail if the version is not set')
        parser.add_argument(
            '-w',
            '--write-file',
            action='store_true',
            help='Write to version file. Implies --raise-error (we never want to write "unknown")',
        )
        parser.add_argument(
            '--version-file-name',
            type=str,
            default=DEFAULT_VERSION_FILE_NAME,
            help='Name of the version file (default: %(default)s)',
        )
        parser.add_argument(
            '--base',
            type=Path,
            default=None,
            help='Optional path to version file',
        )

    def handle(self, **options):
        base = options.get('base')
        if not base:
            base = settings.BASE_DIR
        base_dir = Path(base)
        file_name = options['version_file_name']

        raise_error = options['raise_error'] and options['write_file']

        if options['get_from_file']:
            v = get_version(raise_error=raise_error, base_dir=base_dir, file_name=file_name)
        else:
            v = determine_version(raise_error=raise_error, base_dir=base_dir)

        if options['write_file']:
            version_file = base_dir / file_name
            version_file.write_text(v)
            print(f'Wrote version {v} to {version_file}')
        else:
            print(v)
