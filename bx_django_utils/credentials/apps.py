from django.apps import AppConfig


class CredentialsConfig(AppConfig):
    """
    Credentials AppConfig
    """

    name = 'bx_django_utils.credentials'
    verbose_name = 'Credentials'

    def ready(self):
        # Register system checks:
        import bx_django_utils.credentials.checks  # noqa
