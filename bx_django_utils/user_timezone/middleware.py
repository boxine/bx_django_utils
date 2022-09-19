import logging

import pytz
from django.utils import timezone


logger = logging.getLogger(__name__)


class UserTimezoneMiddleware:
    """
    Activate Timezone by "UserTimeZone" cookie
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if raw_time_zone := request.COOKIES.get('UserTimeZone'):
            try:
                tzinfo = pytz.timezone(raw_time_zone)
            except pytz.exceptions.UnknownTimeZoneError:
                logger.error('Unknown user time zone %r', raw_time_zone)
            else:
                # Response with user timezone:
                with timezone.override(tzinfo):
                    response = self.get_response(request)
                return response

        # Response with default timezone:
        return self.get_response(request)
