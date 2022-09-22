import base64

from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.functional import LazyObject


try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
except ImportError as err:
    raise ImportError(f'Missing "cryptography" package: {err}')


backend = default_backend()


def _make_fernet_key(phrase):
    """
    Derives a 32-bit b64-encoded Fernet key from an arbitrary phrase.
    """
    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        info=getattr(settings, 'CREDENTIALS_INFO_BYTES', None),
        salt=settings.SECRET_KEY.encode(),  # not random because we need reproducible key derivation
        backend=backend,
    )
    return base64.urlsafe_b64encode(hkdf.derive(force_bytes(phrase)))


class _SecretKeyFernet(LazyObject):
    def _setup(self):
        self._wrapped = Fernet(_make_fernet_key(settings.SECRET_KEY))


_fernet = _SecretKeyFernet()


def encrypt(value: str) -> bytes:
    """
    Helper function to Fernet-encrypt a value against Django's SECRET_KEY.
    """
    return _fernet.encrypt(force_bytes(value))


def decrypt(encrypted_value: bytes) -> str:
    """
    Helper function to decrypt a value that was Fernet-encrypted against Django's SECRET_KEY.
    """
    return _fernet.decrypt(encrypted_value).decode()
