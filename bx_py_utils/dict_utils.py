def dict_get(item, *keys):
    """
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
