"""
API app configuration.
API应用配置
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    API应用配置类 (API App Configuration)
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    verbose_name = "REST API接口"
