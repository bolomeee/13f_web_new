"""
Crawler app configuration.
爬虫应用配置
"""

from django.apps import AppConfig


class CrawlerConfig(AppConfig):
    """
    爬虫应用配置类 (Crawler App Configuration)
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "crawler"
    verbose_name = "SEC 13F 爬虫系统"
