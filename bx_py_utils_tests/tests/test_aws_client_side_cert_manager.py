from pathlib import Path
from unittest import mock

import requests
import requests_mock
from django.test import SimpleTestCase

from bx_py_utils.aws.client_side_cert_manager import ClientSideCertManager
from bx_py_utils.test_utils.mock_boto3session import MockedBoto3Session


class ClientSideCertManagerTestCase(SimpleTestCase):
    def test_cert_manager(self):

        def mocked_response(request, context):
            cert = request.cert
            tls_cert_path = Path(cert[0])
            tls_key_path = Path(cert[1])

            with tls_cert_path.open('rb') as f:
                tls_cert = f.read()

            with tls_key_path.open('rb') as f:
                tls_key = f.read()

            assert tls_cert == b'Mocked TLS Cert'
            assert tls_key == b'Mocked TLS Key'

            context.status_code = 200
            context.headers['content-type'] = 'application/json'
            return [tls_cert_path.name, tls_key_path.name]

        with mock.patch('boto3.session.Session', MockedBoto3Session()) as m:
            m.add_secret_binary(
                the_cert=b'Mocked TLS Cert',
                the_key=b'Mocked TLS Key'
            )

            with ClientSideCertManager(
                tls_cert_secret_name='the_cert',
                tls_key_secret_name='the_key',
            ) as cert_manager:
                with requests_mock.mock() as m:
                    m.get('https://foo.tld/bar/', json=mocked_response)
                    response = requests.get(
                        'https://foo.tld/bar/',
                        cert=cert_manager.cert,
                    )

                [tls_cert_file, tls_key_file] = response.json()
                tls_cert_path = Path(tls_cert_file)
                tls_key_path = Path(tls_key_file)

                # This are the created temp files? Check NamedTemporaryFile prefix:
                assert tls_cert_path.name.startswith('tls_cert_')
                assert tls_key_path.name.startswith('tls_key_')

                # Temp files deleted after context manager exit?
                assert not tls_cert_path.is_file()
                assert not tls_key_path.is_file()
