"""
ASGI config for 13F Tracker project.
13F追踪系统的ASGI配置

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_config.settings")

application = get_asgi_application()
