import re
from pathlib import Path

from django.utils.text import slugify


def filename2human_name(filename):
    """
    Convert filename to a capitalized name, e.g.:

    >>> filename2human_name('bar.py')
    'Bar'
    >>> filename2human_name('No file-Extension!')
    'No File Extension'
    >>> filename2human_name('Hör_gut-zu!.aac')
    'Hör Gut Zu'

    Only file names are allowed, no file path:

    >>> filename2human_name('foo/bar.py')
    Traceback (most recent call last):
      ...
    AssertionError: Not valid filename: 'foo/bar.py'
    """
    assert Path(filename).name == filename, f'Not valid filename: {filename!r}'

    txt = filename.partition('.')[0]
    txt = slugify(txt, allow_unicode=True)
    txt = txt.replace('_', ' ').replace('-', ' ')
    txt = ' '.join(word.capitalize() for word in txt.split())
    return txt


def clean_filename(filename):
    """
    Convert filename to ASCII only via slugify, e.g.:

    >>> clean_filename('bar.py')
    'bar.py'
    >>> clean_filename('No-Extension!')
    'no_extension'
    >>> clean_filename('testäöüß!.exe')
    'testaou.exe'
    >>> clean_filename('nameäöü.extäöü')
    'nameaou.extaou'
    >>> clean_filename('g/a\\\\rba:g"\\'e.ext')
    'g_arba_g__e.ext'
    """

    # Strip out path characters
    filename = re.sub(r'[/:\"\']', '_', filename)

    assert Path(filename).name == filename, f'Invalid filename: {filename!r}'

    def convert(txt):
        txt = slugify(txt, allow_unicode=False)
        return txt.replace('-', '_')

    suffix = Path(filename).suffix
    if suffix:
        filename = filename[:-len(suffix)]
        suffix = f'.{convert(suffix)}'
    filename = convert(filename)
    return f'{filename}{suffix}'
