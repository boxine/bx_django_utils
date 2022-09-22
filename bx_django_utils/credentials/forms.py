from bx_py_utils.anonymize import anonymize
from django import forms

from bx_django_utils.credentials.models import Credential


class CredentialForm(forms.ModelForm):
    """
    Model form for Credential that never display a secret in plaintext.
    """

    secret_anonymized = forms.CharField(required=False, disabled=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'secret' in self.initial:
            # Edit existing secret
            self.initial['secret_anonymized'] = anonymize(self.initial['secret'])

            # we never want to show existing secrets in plain text
            self.initial['secret'] = ''
        else:
            # A new secret should be created -> hide the anonymized field:
            self.fields['secret_anonymized'].widget = forms.HiddenInput()

    class Meta:
        model = Credential
        fields = '__all__'
