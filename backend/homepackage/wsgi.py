"""
WSGI config for HomePackage project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homepackage.settings.production')

application = get_wsgi_application()
