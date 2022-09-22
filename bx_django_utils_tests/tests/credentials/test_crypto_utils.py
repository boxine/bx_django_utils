from unittest import TestCase

from cryptography.fernet import Fernet
from django.utils.encoding import force_bytes

from bx_django_utils.credentials.utils import _make_fernet_key, decrypt, encrypt


class CryptoUtilsTestCase(TestCase):
    def test_key_derivation(self):
        fk = _make_fernet_key('someSECRET')
        assert isinstance(fk, bytes)

    def test_key_derivation_is_stable(self):
        key = 'superSECRET123'

        assert _make_fernet_key(key) == _make_fernet_key(key)

    def test_fernet_can_consume_key(self):
        fk = _make_fernet_key('someSECRET')

        Fernet(fk)

    def test_fernet_workflow(self):
        my_secret = 'not for curious eyes'

        f = Fernet(_make_fernet_key('someSECRET'))

        encrypted = f.encrypt(force_bytes(my_secret))
        decrypted = f.decrypt(encrypted)

        assert decrypted.decode() == my_secret

    def test_encryption_helpers(self):
        secret = 'not for curious eyes'

        encrypted = encrypt(secret)
        assert isinstance(encrypted, bytes)

        decrypted = decrypt(encrypted)
        assert decrypted == secret
