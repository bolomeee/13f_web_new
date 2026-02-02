"""
API views for 13F Tracker.
13F追踪系统的API视图

Implements all RESTful endpoints according to the integration specification.
按照集成规范实现所有RESTful端点
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Q, Count
from django.shortcuts import get_object_or_404

from crawler.models import Institution, Filing, Holding, OptionPosition, CrawlLog
from crawler.services import InstitutionService, CrawlLogService
from crawler.tasks import crawl_all_institutions, crawl_single_institution_task

from .serializers import (
    InstitutionSerializer,
    InstitutionDetailSerializer,
    FilingSerializer,
    FilingDetailSerializer,
    HoldingSerializer,
    OptionPositionSerializer,
    CrawlLogSerializer,
    MonitoredCompanySerializer,
    SystemStatusSerializer,
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页配置"""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class InstitutionViewSet(viewsets.ModelViewSet):
    """
    机构视图集 (Institution ViewSet)

    提供机构的CRUD操作
    Provides CRUD operations for institutions
    """

    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action == "retrieve":
            return InstitutionDetailSerializer
        return InstitutionSerializer

    @action(detail=True, methods=["get"])
    def latest_filing(self, request, pk=None):
        """
        获取机构的最新申报文件
        Get latest filing for institution

        GET /api/institutions/{id}/latest_filing/
        """
        institution = self.get_object()
        latest_filing = institution.filings.order_by("-period_of_report").first()

        if not latest_filing:
            return Response(
                {"detail": "No filings found for this institution"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = FilingDetailSerializer(latest_filing)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def trigger_crawl(self, request, pk=None):
        """
        触发单个机构的爬取
        Trigger crawl for single institution

        POST /api/institutions/{id}/trigger_crawl/
        """
        institution = self.get_object()

        # 启动异步任务
        task = crawl_single_institution_task.delay(str(institution.id))

        return Response(
            {"task_id": task.id, "status": "started", "institution": institution.name}
        )


class FilingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    申报文件视图集 (Filing ViewSet)

    只读视图，提供文件查询
    Read-only view for filing queries
    """

    queryset = Filing.objects.all().select_related("institution")
    serializer_class = FilingSerializer
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action == "retrieve":
            return FilingDetailSerializer
        return FilingSerializer

    def get_queryset(self):
        """支持按机构和季度过滤"""
        queryset = super().get_queryset()

        # 按机构过滤
        institution_id = self.request.query_params.get("institution")
        if institution_id:
            queryset = queryset.filter(institution_id=institution_id)

        # 按季度过滤
        quarter = self.request.query_params.get("quarter")
        if quarter:
            queryset = queryset.filter(quarter=quarter)

        return queryset.order_by("-period_of_report")


@api_view(["GET"])
def dashboard_summary(request):
    """
    仪表盘摘要数据
    Dashboard summary data

    GET /api/dashboard/summary

    返回Dashboard所需的所有聚合数据
    Returns all aggregated data needed for Dashboard
    """
    try:
        # 获取最新的Filing（用于计算top picks）
        latest_filings = Filing.objects.order_by("-period_of_report")[:100]

        # 1. Top Picks Cards - 四列数据
        top_picks_cards = []

        # Highest Increase (最大增持)
        highest_increase = Holding.objects.filter(
            filing__in=latest_filings,
            action_type__in=[Holding.ACTION_BUY, Holding.ACTION_NEW],
        ).order_by("-pct_change")[:10]

        top_picks_cards.append(
            {
                "type": "highest_increase",
                "title": "Highest Increase",
                "items": [
                    {
                        "ticker": h.ticker,
                        "name": h.company_name,
                        "institution": h.filing.institution.name,
                        "value": float(h.pct_change) if h.pct_change else 0,
                    }
                    for h in highest_increase
                ],
            }
        )

        # Highest Decrease (最大减持)
        highest_decrease = Holding.objects.filter(
            filing__in=latest_filings, action_type=Holding.ACTION_SELL
        ).order_by("pct_change")[:10]

        top_picks_cards.append(
            {
                "type": "highest_decrease",
                "title": "Highest Decrease",
                "items": [
                    {
                        "ticker": h.ticker,
                        "name": h.company_name,
                        "institution": h.filing.institution.name,
                        "value": float(h.pct_change) if h.pct_change else 0,
                    }
                    for h in highest_decrease
                ],
            }
        )

        # Consensus Buy (共识买入 - 多个机构都在买)
        # 简化实现：找出被多个机构增持的股票
        consensus_buy_tickers = (
            Holding.objects.filter(
                filing__in=latest_filings,
                action_type__in=[Holding.ACTION_BUY, Holding.ACTION_NEW],
            )
            .values("ticker")
            .annotate(count=Count("id"))
            .filter(count__gte=2)
            .order_by("-count")[:10]
        )

        consensus_buy_items = []
        for item in consensus_buy_tickers:
            ticker = item["ticker"]
            holdings = Holding.objects.filter(
                filing__in=latest_filings,
                ticker=ticker,
                action_type__in=[Holding.ACTION_BUY, Holding.ACTION_NEW],
            ).first()

            if holdings:
                consensus_buy_items.append(
                    {
                        "ticker": ticker,
                        "name": holdings.company_name,
                        "institution": f"{item['count']} institutions",
                        "value": item["count"],
                    }
                )

        top_picks_cards.append(
            {
                "type": "consensus_buy",
                "title": "Consensus Buy",
                "items": consensus_buy_items,
            }
        )

        # Consensus Sell (共识卖出)
        consensus_sell_tickers = (
            Holding.objects.filter(
                filing__in=latest_filings,
                action_type__in=[Holding.ACTION_SELL, Holding.ACTION_SOLD_OUT],
            )
            .values("ticker")
            .annotate(count=Count("id"))
            .filter(count__gte=2)
            .order_by("-count")[:10]
        )

        consensus_sell_items = []
        for item in consensus_sell_tickers:
            ticker = item["ticker"]
            holdings = Holding.objects.filter(
                filing__in=latest_filings,
                ticker=ticker,
                action_type__in=[Holding.ACTION_SELL, Holding.ACTION_SOLD_OUT],
            ).first()

            if holdings:
                consensus_sell_items.append(
                    {
                        "ticker": ticker,
                        "name": holdings.company_name,
                        "institution": f"{item['count']} institutions",
                        "value": item["count"],
                    }
                )

        top_picks_cards.append(
            {
                "type": "consensus_sell",
                "title": "Consensus Sell",
                "items": consensus_sell_items,
            }
        )

        # 2. Recent Activity (最近活动)
        recent_activity = []
        recent_holdings = (
            Holding.objects.filter(
                filing__in=latest_filings,
                action_type__in=[
                    Holding.ACTION_BUY,
                    Holding.ACTION_SELL,
                    Holding.ACTION_NEW,
                    Holding.ACTION_SOLD_OUT,
                ],
            )
            .select_related("filing", "filing__institution")
            .order_by("-filing__filing_date")[:50]
        )

        for holding in recent_holdings:
            recent_activity.append(
                {
                    "id": str(holding.id),
                    "guruName": holding.filing.institution.name,
                    "action": holding.action_type.lower(),
                    "ticker": holding.ticker,
                    "changePercent": (
                        float(holding.pct_change) if holding.pct_change else 0
                    ),
                    "date": holding.filing.filing_date.isoformat(),
                }
            )

        return Response(
            {"top_picks_cards": top_picks_cards, "recent_activity": recent_activity}
        )

    except Exception as e:
        logger.error(f"❌ 获取仪表盘数据失败: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def institution_detail(request, institution_id):
    """
    机构详情
    Institution details

    GET /api/institutions/{id}

    返回单个机构的详情页数据
    Returns detail page data for single institution
    """
    institution = get_object_or_404(Institution, id=institution_id)
    serializer = InstitutionDetailSerializer(institution)
    return Response(serializer.data)


@api_view(["GET"])
def admin_companies(request):
    """
    获取监控公司列表
    Get monitored companies list

    GET /api/admin/companies
    """
    institutions = Institution.objects.all().order_by("-created_at")

    data = [
        {
            "id": str(inst.id),
            "cik": inst.cik,
            "name": inst.name,
            "is_active": inst.is_active,
            "last_update": inst.updated_at,
        }
        for inst in institutions
    ]

    return Response(data)


@api_view(["POST"])
def admin_add_company(request):
    """
    添加监控公司
    Add monitored company

    POST /api/admin/companies
    Body: {"cik": "0001067983"} or {"ticker": "BRK-B"}
    """
    cik = request.data.get("cik")
    ticker = request.data.get("ticker")

    if not cik and not ticker:
        return Response(
            {"error": "CIK or ticker is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        institution_service = InstitutionService()

        # 如果提供的是ticker，先查找CIK
        if ticker and not cik:
            cik = institution_service.lookup_cik(ticker)
            if not cik:
                return Response(
                    {"error": f"CIK not found for ticker: {ticker}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # 创建或获取机构
        institution = institution_service.get_or_create_institution(cik)

        serializer = InstitutionSerializer(institution)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"❌ 添加公司失败: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
def admin_delete_company(request, company_id):
    """
    删除监控公司
    Delete monitored company

    DELETE /api/admin/companies/{id}

    级联删除该机构及其所有Filing、Holding数据
    Cascade delete institution and all related Filing, Holding data
    """
    try:
        institution = get_object_or_404(Institution, id=company_id)
        institution_name = institution.name
        institution.delete()

        logger.info(f"🗑️ 删除机构: {institution_name}")
        return Response({"message": f"Successfully deleted {institution_name}"})

    except Exception as e:
        logger.error(f"❌ 删除公司失败: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def admin_system_status(request):
    """
    获取系统状态
    Get system status

    GET /api/admin/system-status
    """
    try:
        stats = CrawlLogService.get_statistics()

        # 获取最后一次爬取时间
        last_log = CrawlLog.objects.order_by("-timestamp").first()

        # 统计总数
        total_institutions = Institution.objects.count()
        total_filings = Filing.objects.count()

        return Response(
            {
                "success_count": stats["success_count"],
                "error_count": stats["error_count"],
                "last_crawl_time": last_log.timestamp if last_log else None,
                "total_institutions": total_institutions,
                "total_filings": total_filings,
            }
        )

    except Exception as e:
        logger.error(f"❌ 获取系统状态失败: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def crawler_trigger(request):
    """
    手动触发爬虫更新
    Manually trigger crawler update

    POST /api/crawler/trigger
    """
    try:
        # 启动异步任务
        task = crawl_all_institutions.delay()

        logger.info(f"🚀 手动触发爬虫任务: {task.id}")

        return Response(
            {
                "task_id": task.id,
                "status": "started",
                "message": "Crawler task has been started",
            }
        )

    except Exception as e:
        logger.error(f"❌ 触发爬虫失败: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def crawler_status(request, task_id):
    """
    查询爬虫任务状态
    Query crawler task status

    GET /api/crawler/status/{task_id}
    """
    from celery.result import AsyncResult

    try:
        task_result = AsyncResult(task_id)

        return Response(
            {
                "task_id": task_id,
                "status": task_result.status,
                "result": task_result.result if task_result.ready() else None,
            }
        )

    except Exception as e:
        logger.error(f"❌ 查询任务状态失败: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
