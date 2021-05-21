from unittest import mock

from django.test import SimpleTestCase

from bx_django_utils.aws.secret_manager import SecretsManager
from bx_django_utils.test_utils.mock_aws_secret_manager import SecretsManagerMock
from bx_django_utils.test_utils.mock_boto3session import MockedBoto3Session


class SecretManagerTestCase(SimpleTestCase):
    def test_get_secret_string(self):
        with mock.patch('boto3.session.Session', MockedBoto3Session()) as m:
            m.add_secret_string(foo='bar')

            manager = SecretsManager(region_name='eu-central-1')
            secret = manager.get_secret(secret_name='foo')
            assert secret == 'bar'
            secret = manager.get_secret(secret_name='foo', force_bytes=True)
            assert secret == b'bar'

    def test_get_secret_binary(self):
        with mock.patch('boto3.session.Session', MockedBoto3Session()) as m:
            m.add_secret_binary(foo=b'bar')

            manager = SecretsManager(region_name='eu-central-1')
            secret = manager.get_secret(secret_name='foo')
            assert secret == b'bar'
            secret = manager.get_secret(secret_name='foo', force_str=True)
            assert secret == 'bar'

    def test_secret_manager_mock(self):
        with mock.patch(
            'bx_django_utils.aws.secret_manager.SecretsManager', SecretsManagerMock(foo='bar')
        ):
            from bx_django_utils.aws.secret_manager import SecretsManager
            manager = SecretsManager(region_name='eu-central-1')
            secret = manager.get_secret(secret_name='foo')
            assert secret == 'bar'
