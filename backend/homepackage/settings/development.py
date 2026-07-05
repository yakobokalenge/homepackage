"""
Development settings for HomePackage.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ['*']

# Use console email backend in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Add debug toolbar in development
INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405

INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Add browsable API renderer in development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

# Disable throttling in development
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # noqa: F405

# Use local file storage instead of Cloudinary in development
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# CORS allow all in development
CORS_ALLOW_ALL_ORIGINS = True
