# bx_django_utils - User Timezone

Automatic activation of the time zone for the current user.


## how it works

1. Store the current user timezone via JavaScript into a Cookie.
2. A middleware activates the user timezone from the Cookie.

Limitation: The time zone is switched only from the second request!


## how to use

Change your `settings`, e.g.:
```python
INSTALLED_APPS = [
    # ...
    'bx_django_utils.user_timezone.apps.UserTimezoneAppConfig',
    # ...
]

MIDDLEWARE = [
    # ...
    'bx_django_utils.user_timezone.middleware.UserTimezoneMiddleware',
    # ...
]
```

Load the JavaScript on a central page (e.g. on your login page or the admin index etc.):
```html
<script src="{% static 'user_timezone.js' %}"></script>
```

To display the current Timezone, use the normal Django way, e.g.:
```html
{% load tz %}

<p>{% trans "Active Timezone:" %} {% get_current_timezone as TIME_ZONE %}{{ TIME_ZONE }}</p>
```
