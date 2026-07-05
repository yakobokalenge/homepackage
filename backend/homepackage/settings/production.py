"""
Production settings for HomePackage.
"""
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F401,F403

DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Sentry error tracking
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')  # noqa: F405
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Static files served by whitenoise or S3
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Logging for production
LOGGING['handlers']['file'] = {  # noqa: F405
    'class': 'logging.FileHandler',
    'filename': os.environ.get('LOG_FILE', '/var/log/homepackage/app.log'),  # noqa: F405
    'formatter': 'verbose',
}
LOGGING['root']['handlers'].append('file')  # noqa: F405
