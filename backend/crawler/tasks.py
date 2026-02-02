"""
Celery tasks for crawler operations.
爬虫操作的Celery异步任务

This module defines asynchronous tasks for:
- Crawling all monitored institutions
- Crawling single institution
- Periodic updates
"""

import logging
from celery import shared_task
from django.utils import timezone

from .models import Institution, CrawlLog
from .services import FilingService, CrawlLogService
from .edgar_downloader import EDGARReportDownloader
from .sec_13f_extractor import SEC13FExtractor

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def crawl_all_institutions(self):
    """
    爬取所有激活的机构
    Crawl all active institutions

    这是主要的定时任务，会被Celery Beat调度执行
    This is the main periodic task scheduled by Celery Beat
    """
    task_id = self.request.id
    logger.info(f"🚀 开始爬取所有机构 (Task ID: {task_id})")

    # 创建日志记录
    log = CrawlLogService.create_log(status=CrawlLog.STATUS_RUNNING, task_id=task_id)

    try:
        # 获取所有激活的机构
        institutions = Institution.objects.filter(is_active=True)
        total_filings = 0

        logger.info(f"📊 找到 {institutions.count()} 个激活的机构")

        for institution in institutions:
            try:
                # 爬取单个机构
                filings_count = crawl_single_institution_sync(institution)
                total_filings += filings_count
                logger.info(f"✅ {institution.name}: 处理了 {filings_count} 个文件")
            except Exception as e:
                logger.error(f"❌ 爬取 {institution.name} 失败: {e}")
                continue

        # 更新日志状态
        log.status = CrawlLog.STATUS_SUCCESS
        log.filings_processed = total_filings
        log.save()

        logger.info(f"🎉 爬取完成！总共处理了 {total_filings} 个文件")
        return {
            "status": "success",
            "filings_processed": total_filings,
            "institutions_count": institutions.count(),
        }

    except Exception as e:
        logger.error(f"❌ 爬取任务失败: {e}")

        # 更新日志状态
        log.status = CrawlLog.STATUS_ERROR
        log.error_message = str(e)
        log.save()

        # 重试任务
        raise self.retry(exc=e, countdown=300)  # 5分钟后重试


@shared_task(bind=True)
def crawl_single_institution_task(self, institution_id: str):
    """
    爬取单个机构（异步任务版本）
    Crawl single institution (async task version)

    Args:
        institution_id: Institution UUID
    """
    try:
        institution = Institution.objects.get(id=institution_id)
        filings_count = crawl_single_institution_sync(institution)

        return {
            "status": "success",
            "institution": institution.name,
            "filings_processed": filings_count,
        }
    except Institution.DoesNotExist:
        logger.error(f"❌ 机构不存在: {institution_id}")
        return {"status": "error", "message": "Institution not found"}
    except Exception as e:
        logger.error(f"❌ 爬取机构失败: {e}")
        raise


def crawl_single_institution_sync(institution: Institution) -> int:
    """
    爬取单个机构（同步函数）
    Crawl single institution (synchronous function)

    Args:
        institution: Institution instance

    Returns:
        Number of filings processed
    """
    logger.info(f"🔍 开始爬取机构: {institution.name} (CIK: {institution.cik})")

    try:
        # 使用EDGARCrawlerService进行爬取
        from .edgar_service import EDGARCrawlerService

        crawler = EDGARCrawlerService()

        # 爬取最近4个季度的13F文件
        filings_count = crawler.crawl_institution_13f(
            institution=institution, max_filings=4
        )

        logger.info(f"✅ 成功爬取 {institution.name}，处理了 {filings_count} 个文件")
        return filings_count

    except Exception as e:
        logger.error(f"❌ 爬取 {institution.name} 时出错: {e}")
        raise


@shared_task
def cleanup_old_logs():
    """
    清理旧的爬虫日志
    Cleanup old crawl logs

    保留最近30天的日志
    Keep logs from last 30 days
    """
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count, _ = CrawlLog.objects.filter(timestamp__lt=cutoff_date).delete()

    logger.info(f"🧹 清理了 {deleted_count} 条旧日志")
    return {"deleted_count": deleted_count}


@shared_task
def update_institution_aum():
    """
    更新所有机构的AUM（资产管理规模）
    Update AUM for all institutions

    基于最新的13F文件计算总资产
    Calculate total assets based on latest 13F filing
    """
    from django.db.models import Sum

    institutions = Institution.objects.filter(is_active=True)
    updated_count = 0

    for institution in institutions:
        # 获取最新的Filing
        latest_filing = institution.filings.order_by("-period_of_report").first()

        if latest_filing:
            # 计算总市值
            total_value = (
                latest_filing.holdings.aggregate(total=Sum("value"))["total"] or 0
            )

            institution.aum = total_value
            institution.save(update_fields=["aum"])
            updated_count += 1

    logger.info(f"📊 更新了 {updated_count} 个机构的AUM")
    return {"updated_count": updated_count}
