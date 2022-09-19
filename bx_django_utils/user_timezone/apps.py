from django.apps import AppConfig


class UserTimezoneAppConfig(AppConfig):
    """
    Django app to set the user local time zone.
    """

    name = 'bx_django_utils.user_timezone'
    verbose_name = "User Timezone"

    def ready(self):
        # Register system checks:
        import bx_django_utils.user_timezone.checks  # noqa
