from django.conf import settings
from django.core.checks import Error, register


@register()
def credentials_check(app_configs, **kwargs):
    errors = []

    try:
        import cryptography  # noqa:F401
    except ImportError as err:
        errors.append(
            Error(
                msg=f'Package "cryptography" is not installed: {err}',
                hint='Add "cryptography" to your project requirements.',
                id='credentials.E001',
            )
        )

    info = getattr(settings, 'CREDENTIALS_INFO_BYTES', None)
    if info is not None and not isinstance(info, bytes):
        errors.append(
            Error(
                msg='settings.CREDENTIALS_INFO_BYTES must be None or bytes!',
                id='credentials.E002',
            )
        )

    return errors
