from django.test import TestCase

from bx_django_utils.credentials.forms import CredentialForm
from bx_django_utils.credentials.models import Credential


class CredentialFormTestCase(TestCase):
    def test_secret_is_initially_hidden(self):
        cred = Credential(key='SOME_CREDENTIAL', secret='superSECRET123')

        form = CredentialForm(instance=cred)

        assert form.initial['key'] == cred.key
        assert form.initial['secret'] == ''
