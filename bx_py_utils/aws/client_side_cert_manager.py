import tempfile

from bx_py_utils.aws.secret_manager import SecretsManager


class ClientSideCertManager:
    """
    Helper to manage client-side TLS certificate via AWS Secrets Manager by
    storing the cert/key content in a temporary file.

    Libraries like "requests" any many others needs the client-side TLS certificate as files.
    They don't accept cert/key as strings. So we have to fetch the content from AWS and
    store them in a file.

    Usage e.g.:

        with ClientSideCertManager(
            tls_cert_secret_name='foo',
            tls_key_secret_name='bar',
            region_name='eu-central-1'
        ) as cert_manager:
            response = requests.get(
                'https://foo.tld/bar/',
                cert=cert_manager.cert,
            )
    """

    def __init__(self, *, tls_cert_secret_name, tls_key_secret_name, region_name):
        self._tls_cert_secret_name = tls_cert_secret_name
        self._tls_key_secret_name = tls_key_secret_name

        self._secrets_manager = SecretsManager(region_name=region_name)
        self._tls_cert_file = None
        self._tls_key_file = None

        self.cert = None

    def _store_secret(self, secret_name, temp_file):
        secret = self._secrets_manager.get_secret(
            secret_name=secret_name,
            force_bytes=True
        )
        assert secret, f'No {secret_name!r} secret !'

        temp_file.write(secret)
        temp_file.flush()

    def __enter__(self):
        # Store TLS certificate:
        self._tls_cert_file = tempfile.NamedTemporaryFile(prefix='tls_cert_')
        self._store_secret(
            secret_name=self._tls_cert_secret_name,
            temp_file=self._tls_cert_file,
        )

        # Store TLS key:
        self._tls_key_file = tempfile.NamedTemporaryFile(prefix='tls_key_')
        self._store_secret(
            secret_name=self._tls_key_secret_name,
            temp_file=self._tls_key_file,
        )

        self.cert = (self._tls_cert_file.name, self._tls_key_file.name)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._tls_cert_file is not None:
            self._tls_cert_file.close()

        if self._tls_key_file is not None:
            self._tls_key_file.close()
