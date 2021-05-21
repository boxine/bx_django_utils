from typing import Iterable


def dict_get(item, *keys):
    """
    nested dict `get()`

    >>> example={1: {2: 'X'}}
    >>> dict_get(example, 1, 2)
    'X'
    >>> dict_get(example, 1)
    {2: 'X'}
    >>> dict_get(example, 1, 2, 3) is None
    True
    >>> dict_get(example, 'foo', 'bar') is None
    True
    >>> dict_get('no dict', 'no key') is None
    True
    """
    for key in keys:
        if isinstance(item, dict):
            item = item.get(key)
        else:
            return None
    return item


def pluck(obj: dict, keys: Iterable[str]):
    """
    Extract values from a dict, if they are present

    >>> pluck({'a': 1, 'b': 2}, ['a', 'c'])
    {'a': 1}
    """
    assert isinstance(obj, dict)
    res = {}
    for k in keys:
        if k in obj:
            res[k] = obj[k]
    return res
