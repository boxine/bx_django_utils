# bx_django_utils - Credentials

A Django App to store key-value-pairs encrypted, using [Fernet symmetric encryption](https://cryptography.io/en/latest/fernet/) from [Cryptography](https://github.com/pyca/cryptography) project.

Note:

* `salt` and `key` depends only on `settings.SECRET_KEY` (So this **must** be keep secret!)
* Only a `superuser` can view/edit/delete Credentials in Admin.
* The `secret` checks multiple sources, in this order:
  1. The database (Credentials model)
  2. Django settings module
  3. environment variables


## setup


### requirements

Add PyPi package [cryptography](https://github.com/pyca/cryptography) to your project requirements.


### settings.py

Add `admin_extra_views` to `INSTALLED_APPS`, e.g.:

```python
INSTALLED_APPS = [
    # ...
    'bx_django_utils.credentials',
    # ...
]

# Optional info for all credentials secrets:
CREDENTIALS_INFO_BYTES = b'Just a info'
```

## usage

e.g.:

```python
from bx_django_utils.credentials.models import Credential

def your_view(request):
    # Get one secret:
    plaintext_secret = Credential.get('foobar')

    # Get more than one secret:
    username, password = Credential.get_many('username', 'password')
```
