import logging
import re
import zoneinfo

from django.utils import timezone


logger = logging.getLogger(__name__)


class InvalidUserTimeZone(ValueError):
    pass


def validate(raw_time_zone: str, min_length: int, max_length: int, usertimezone_re: str) -> None:
    """
    Validate the UserTimeZone cookie value.
    """
    length = len(raw_time_zone)

    if length > max_length:
        raise InvalidUserTimeZone(f'Expected max length {max_length}, got {length}')

    if length < min_length:
        raise InvalidUserTimeZone(f'Expected min length {min_length}, got {length}')

    if not raw_time_zone.isascii():
        raise InvalidUserTimeZone('Only ASCII chars allowed')

    if not re.fullmatch(usertimezone_re, raw_time_zone):
        raise InvalidUserTimeZone(f'Not match: {raw_time_zone}')


class UserTimezoneMiddleware:
    """
    Activate Timezone by "UserTimeZone" cookie
    """

    MIN_LENGTH = 2  # e.g.: "NZ", "GB", etc.
    MAX_LENGTH = 32  # e.g.: "America/Argentina/ComodRivadavia"
    USERTIMEZONE_RE = r'[a-zA-Z0-9_\-\+/]+'  # e.g.: "Etc/GMT+10", "US/East-Indiana", "Europe/San_Marino"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if raw_time_zone := request.COOKIES.get('UserTimeZone'):
            self.validate(raw_time_zone)
            try:
                tzinfo = zoneinfo.ZoneInfo(raw_time_zone)
            except zoneinfo.ZoneInfoNotFoundError:
                logger.error('Unknown user time zone %r', raw_time_zone)
            else:
                # Response with user timezone:
                with timezone.override(tzinfo):
                    response = self.get_response(request)
                return response

        # Response with default timezone:
        return self.get_response(request)

    def validate(self, raw_time_zone):
        validate(
            raw_time_zone=raw_time_zone,
            min_length=self.MIN_LENGTH,
            max_length=self.MAX_LENGTH,
            usertimezone_re=self.USERTIMEZONE_RE,
        )
