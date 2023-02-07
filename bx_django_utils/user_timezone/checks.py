import zoneinfo

from django.conf import settings
from django.core.checks import Error, Warning, register


MIDDLEWARE_STR = 'bx_django_utils.user_timezone.middleware.UserTimezoneMiddleware'


@register()
def user_timezone_check(app_configs, **kwargs):
    errors = []

    if MIDDLEWARE_STR not in settings.MIDDLEWARE:
        errors.append(
            Warning(
                msg='Missing UserTimezoneMiddleware',
                hint=f'Add "{MIDDLEWARE_STR}" to your settings.',
                id='user_timezone.W001',
            )
        )

    if not hasattr(settings, 'VISIBLE_TIMEZONES'):
        errors.append(
            Error(
                msg='Your settings has no "VISIBLE_TIMEZONES" defined!',
                hint="e.g.: VISIBLE_TIMEZONES = ['Europe/Berlin', 'America/Los_Angeles']",
                id='user_timezone.E001',
            )
        )
    else:
        for tz_name in settings.VISIBLE_TIMEZONES:
            try:
                zoneinfo.ZoneInfo(tz_name)
            except zoneinfo.ZoneInfoNotFoundError:
                errors.append(
                    Error(
                        msg=f'settings.VISIBLE_TIMEZONES entry: {tz_name!r} is invalid!',
                        id='user_timezone.E002',
                    )
                )

    return errors
