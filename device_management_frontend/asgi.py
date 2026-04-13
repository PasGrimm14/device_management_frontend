"""
ASGI config for device_management_frontend project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'device_management_frontend.settings')

application = get_asgi_application()
