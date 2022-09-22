import os

import pytest
from django.test import TestCase, override_settings

from bx_django_utils.credentials.models import Credential


class CredentialTestCase(TestCase):
    def test_get_from_db(self):
        key = 'FOO'
        secret = 'bar'

        Credential.objects.create(key=key, secret=secret)

        assert Credential.get(key) == secret

    def test_get_from_environ(self):
        key = 'DOES_NOT_EXIST_IN_DB_BUT_ENV'
        secret = 'bar'

        os.environ[key] = secret

        with pytest.raises(Credential.DoesNotExist):
            Credential.objects.get(key=key)

        assert Credential.get(key) == secret

    @override_settings(DOES_NOT_EXIST_IN_DB_AND_ENV_BUT_SETTINGS='bar')
    def test_get_from_settings(self):
        key = 'DOES_NOT_EXIST_IN_DB_AND_ENV_BUT_SETTINGS'
        secret = 'bar'

        with pytest.raises(Credential.DoesNotExist):
            Credential.objects.get(key=key)

        assert key not in os.environ

        assert Credential.get(key) == secret

    def test_get_with_no_result(self):
        assert Credential.objects.count() == 0

        with pytest.raises(ValueError):
            Credential.get('DOES_NOT_EXIST')

    @override_settings(CREDENTIAL_IN_SETTINGS='settings')
    def test_get_many_from_mixed(self):
        db_cred = Credential.objects.create(key='CREDENTIAL_IN_DB', secret='db')
        env_key = 'CREDENTIAL_IN_ENV'
        env_secret = 'env'
        os.environ[env_key] = env_secret
        settings_key = 'CREDENTIAL_IN_SETTINGS'
        settings_secret = 'settings'

        first, second, third = Credential.get_many(db_cred.key, env_key, settings_key)

        assert first == db_cred.secret
        assert second == env_secret
        assert third == settings_secret

    @override_settings(FOO='')
    def test_get_many_check(self):
        os.environ['BAR'] = ''
        try:
            with self.assertRaisesMessage(AssertionError, 'FOO not set, BAR not set'):
                Credential.get_many('FOO', 'BAR')
        finally:
            del os.environ['BAR']
