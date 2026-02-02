"""
Celery configuration for 13F Tracker project.
13F追踪系统的Celery配置

This module contains the Celery application instance and configuration.
"""

import os
from celery import Celery
from celery.schedules import crontab

# 设置Django settings模块 (Set the default Django settings module)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_config.settings")

# 创建Celery应用实例 (Create Celery application instance)
app = Celery("institutional_13f_tracker")

# 从Django settings加载配置 (Load configuration from Django settings)
# namespace='CELERY' 表示所有celery相关配置都以CELERY_开头
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现所有已安装app中的tasks.py (Auto-discover tasks from all installed apps)
app.autodiscover_tasks()

# 定时任务配置 (Periodic task configuration)
app.conf.beat_schedule = {
    # 每日更新任务 - 凌晨2点执行 (Daily update task - runs at 2 AM)
    "daily-crawl-all-institutions": {
        "task": "crawler.tasks.crawl_all_institutions",
        "schedule": crontab(hour=2, minute=0),
        "options": {"expires": 3600 * 12},  # 12小时后过期
    },
    # 每周更新任务 - 每周五下午5点执行 (Weekly update - runs every Friday at 5 PM)
    "weekly-crawl-all-institutions": {
        "task": "crawler.tasks.crawl_all_institutions",
        "schedule": crontab(day_of_week=5, hour=17, minute=0),
        "options": {"expires": 3600 * 24},  # 24小时后过期
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    调试任务 (Debug task)
    用于测试Celery是否正常工作
    """
    print(f"Request: {self.request!r}")
