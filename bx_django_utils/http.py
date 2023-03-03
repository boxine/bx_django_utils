from django.http import QueryDict


def build_url_parameters(safe_=None, **params):
    """
    Return an encoded string of all given parameters.

    >>> build_url_parameters(foo=1, bar='<code>')
    'bar=%3Ccode%3E&foo=1'

    List and tuples can be also used, e.g.:

    >>> build_url_parameters(foo=(1,2), bar=[3,4])
    'bar=3&bar=4&foo=1&foo=2'

    `safe_` specifies characters which don't require quoting, e.g.:

    >>> build_url_parameters(next='/foo&bar/')
    'next=%2Ffoo%26bar%2F'

    >>> build_url_parameters(next='/foo&bar/', safe_='/')
    'next=/foo%26bar/'
    """
    query = QueryDict(mutable=True)
    for key, value in sorted(params.items()):
        if isinstance(value, (tuple, list)):
            query.setlist(key, value)
        else:
            query[key] = value
    return query.urlencode(safe=safe_)
