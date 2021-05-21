import hashlib
import string


# Remove umlauts will hopefully avoid to generate valid words ;)
ALPHABET = (
    '-._~'  # Allowed additional characters RFC 3986
    'bcdfghjklmnpqrstvwxyz'  # lower case letters without aeiou
    'BCDFGHJKLMNPQRSTVWXYZ'  # upper case letters without AEIOU
) + string.digits


def url_safe_encode(data, alphabet=ALPHABET):
    """
    Encode bytes into a URL safe string.
    Note:
        Use a URL safe alphabet (see RFC 3986) without umlauts
    """
    assert isinstance(data, bytes)

    len_alphabet = len(alphabet)
    return ''.join(alphabet[char % len_alphabet] for char in data)


def url_safe_hash(data, max_size=None, hasher_name='sha3_512', encoding='utf-8'):
    """
    >>> url_safe_hash('foo', max_size=16)
    'tMXtn6KpcjzTdzTk'
    """
    if isinstance(data, str):
        data = bytes(data, encoding=encoding)

    # Generate hash digest:
    hasher = hashlib.new(hasher_name)
    hasher.update(data)
    hash_digest = hasher.digest()

    # Convert hash digest bytes into URL safe string:
    safe_hash = url_safe_encode(hash_digest)
    if max_size:
        assert len(safe_hash) >= max_size, 'Hash digest too short for requested max size!'
        safe_hash = safe_hash[:max_size]

    return safe_hash
