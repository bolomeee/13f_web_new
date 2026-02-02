"""
project_config package
项目配置包

This will make sure the Celery app is always imported when
Django starts so that shared_task will use this app.
确保Django启动时导入Celery应用，以便shared_task使用此应用。
"""

# 导入Celery应用 (Import Celery app)
from .celery import app as celery_app

__all__ = ("celery_app",)
