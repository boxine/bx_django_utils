import itertools


def chunk_iterable(iterable, chunk_size):
    """
    Returns a generator that yields slices of iterable of the given chunk_size.

    Basic example:
    >>> list(chunk_iterable(range(6), 2))
    [(0, 1), (2, 3), (4, 5)]

    Remaining elements that don't fill a full chunk are returned gracefully:
    >>> list(chunk_iterable(range(5), 2))
    [(0, 1), (2, 3), (4,)]
    """
    iterator = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(iterator, chunk_size))
        if not chunk:
            return  # exit the endless loop!
        yield chunk
