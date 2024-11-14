import functools
import pathlib
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand


VERSION_FILE = pathlib.Path(settings.BASE_DIR) / 'VERSION'


@functools.lru_cache
def get_version(raise_error=False):
    try:
        version_text = VERSION_FILE.read_text()
        return version_text.strip()
    except OSError:
        pass

    return determine_version(raise_error=raise_error)


def determine_version(raise_error=False):
    return _git_version(settings.BASE_DIR, raise_error=raise_error)


def _git_version(cwd, raise_error=False):
    try:
        tags_str = subprocess.check_output(['git', 'tag', '--points-at', 'HEAD'], cwd=cwd).decode('utf-8').strip()
        sha = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=cwd).decode('utf-8').strip()

        names = tags_str.split() + [sha]
        res = '/'.join(names)

        status = subprocess.check_output(['git', 'status', '--untracked-files=no', '--porcelain'], cwd=cwd).decode(
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
            help=f'Write to version file ({VERSION_FILE}). Implies --raise-error (we never want to write "unknown")',
        )

    def handle(self, **options):
        func = get_version if options['get_from_file'] else determine_version
        raise_error = options['raise_error'] and options['write_file']
        v = func(raise_error=raise_error)

        if options['write_file']:
            VERSION_FILE.write_text(v)
            print(f'Wrote version {v} to {VERSION_FILE}')
        else:
            print(v)
