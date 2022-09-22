from django.test import TestCase

from bx_django_utils.credentials.models import Credential


class EncryptedCharFieldTestCase(TestCase):
    def test_orm_behaviour(self):
        # create
        cred = Credential.objects.create(key='FOO', secret='bar')
        assert isinstance(cred.secret, str)
        assert cred.secret == 'bar'

        # refresh
        cred.refresh_from_db()
        assert isinstance(cred.secret, str)
        assert cred.secret == 'bar'

        # update
        Credential.objects.filter(key='FOO').update(secret='foobar')

        # select
        cred = Credential.objects.get(key='FOO')
        assert cred.secret == 'foobar'
