"""
URL configuration for 13F Tracker project.
13F追踪系统的URL路由配置

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin (Django管理后台)
    path("admin/", admin.site.urls),
    # API endpoints (API接口)
    path("api/", include("api.urls")),
]

# 开发环境下提供静态文件服务 (Serve static files in development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
