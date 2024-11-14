"""
    Django settings for bx_django_utils test project.
"""
import os
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'Only a test project!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #
    'debug_toolbar',
    #
    # Own Apps:
    'bx_django_utils',
    'bx_django_utils.approve_workflow',
    'bx_django_utils_tests.test_app',
    'bx_django_utils_tests.approve_workflow_test_app',
    #
    # Admin extra views demo:
    'bx_django_utils.admin_extra_views.apps.AdminExtraViewsAppConfig',
    'bx_django_utils.admin_extra_views.admin_config.CustomAdminConfig',
    #
    # User Timezone:
    'bx_django_utils.user_timezone.apps.UserTimezoneAppConfig',
    #
    # Feature Flags:
    'bx_django_utils.feature_flags.apps.FeatureFlagsAppConfig',
    #
    # Generic Model Filter:
    'bx_django_utils.generic_model_filter.apps.GenericModelFilterAppConfig',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #
    # User Timezone:
    'bx_django_utils.user_timezone.middleware.UserTimezoneMiddleware',
]

# We're a test application, the Debug toolbar is fine to run
DEBUG_TOOLBAR_CONFIG = {
    'IS_RUNNING_TESTS': False,
}

ROOT_URLCONF = 'bx_django_utils_tests.test_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR / 'test_project' / 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bx_django_utils_tests.test_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db.sqlite3'),
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
AUTH_PASSWORD_VALIDATORS = []  # Just a test project, so no restrictions


# Internationalization

LANGUAGE_CODE = 'en-us'
USE_I18N = True
LOCALE_PATHS = (
    BASE_DIR.parent / 'bx_django_utils' / 'locale',
)

TIME_ZONE = 'UTC'
USE_TZ = True
VISIBLE_TIMEZONES = ['Europe/Berlin', 'America/Los_Angeles']


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'


INTERNAL_IPS = [
    '127.0.0.1',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {module}.{funcName} {message}',
            'style': '{',
        },
    },
    'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'}},
    'loggers': {
        '': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'django.auth': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'django.security': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'bx_django_utils': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
    },
}


if os.environ.get('RAISE_LOG_OUTPUT') in ('1', 'true'):
    # Raise an error on every uncaptured log message
    LOGGING['handlers']['raise_error'] = {
        'class': 'bx_py_utils.test_utils.log_utils.RaiseLogUsage',
    }
    for logger_cfg in LOGGING['loggers'].values():
        logger_cfg['handlers'] = ['raise_error']


# Playwright browser tests
# ----------------------------------------------------------------------------
# Avoid django.core.exceptions.SynchronousOnlyOperation. Playwright uses an event loop,
# even when using the sync API. Django only checks whether _any_ event loop is running,
# but not if _itself_ is running in an even loop.
# see https://github.com/microsoft/playwright-python/issues/439#issuecomment-763339612.
os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', '1')
