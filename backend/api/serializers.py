"""
Serializers for API endpoints.
API端点的序列化器

Converts Django models to/from JSON format.
将Django模型转换为JSON格式
"""

from rest_framework import serializers
from crawler.models import Institution, Filing, Holding, OptionPosition, CrawlLog


class InstitutionSerializer(serializers.ModelSerializer):
    """
    机构序列化器 (Institution Serializer)
    """

    class Meta:
        model = Institution
        fields = [
            "id",
            "cik",
            "name",
            "avatar_initials",
            "aum",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HoldingSerializer(serializers.ModelSerializer):
    """
    持仓明细序列化器 (Holding Serializer)
    """

    class Meta:
        model = Holding
        fields = [
            "id",
            "ticker",
            "company_name",
            "cusip",
            "share_count",
            "value",
            "pct_portfolio",
            "share_change",
            "pct_change",
            "action_type",
            "created_at",
        ]


class OptionPositionSerializer(serializers.ModelSerializer):
    """
    期权持仓序列化器 (Option Position Serializer)
    """

    class Meta:
        model = OptionPosition
        fields = [
            "id",
            "ticker",
            "option_type",
            "contracts",
            "notional_value",
            "created_at",
        ]


class FilingSerializer(serializers.ModelSerializer):
    """
    申报文件序列化器 (Filing Serializer)
    """

    institution_name = serializers.CharField(source="institution.name", read_only=True)
    holdings_count = serializers.SerializerMethodField()
    options_count = serializers.SerializerMethodField()

    class Meta:
        model = Filing
        fields = [
            "id",
            "institution",
            "institution_name",
            "period_of_report",
            "filing_date",
            "accession_number",
            "quarter",
            "holdings_count",
            "options_count",
            "created_at",
        ]

    def get_holdings_count(self, obj):
        """获取持仓数量"""
        return obj.holdings.count()

    def get_options_count(self, obj):
        """获取期权数量"""
        return obj.option_positions.count()


class FilingDetailSerializer(serializers.ModelSerializer):
    """
    申报文件详情序列化器（包含持仓明细）
    Filing Detail Serializer (with holdings)
    """

    institution = InstitutionSerializer(read_only=True)
    holdings = HoldingSerializer(many=True, read_only=True)
    option_positions = OptionPositionSerializer(many=True, read_only=True)

    class Meta:
        model = Filing
        fields = [
            "id",
            "institution",
            "period_of_report",
            "filing_date",
            "accession_number",
            "quarter",
            "holdings",
            "option_positions",
            "created_at",
        ]


class InstitutionDetailSerializer(serializers.ModelSerializer):
    """
    机构详情序列化器（包含最新持仓）
    Institution Detail Serializer (with latest holdings)
    """

    increased_positions = serializers.SerializerMethodField()
    decreased_positions = serializers.SerializerMethodField()
    call_options = serializers.SerializerMethodField()
    put_options = serializers.SerializerMethodField()
    latest_filing_quarter = serializers.SerializerMethodField()

    class Meta:
        model = Institution
        fields = [
            "id",
            "cik",
            "name",
            "avatar_initials",
            "aum",
            "is_active",
            "latest_filing_quarter",
            "increased_positions",
            "decreased_positions",
            "call_options",
            "put_options",
            "created_at",
            "updated_at",
        ]

    def get_latest_filing(self, obj):
        """获取最新的Filing"""
        return obj.filings.order_by("-period_of_report").first()

    def get_latest_filing_quarter(self, obj):
        """获取最新申报季度"""
        latest = self.get_latest_filing(obj)
        return latest.quarter if latest else None

    def get_increased_positions(self, obj):
        """获取加仓持仓"""
        latest = self.get_latest_filing(obj)
        if not latest:
            return []

        holdings = latest.holdings.filter(
            action_type__in=[Holding.ACTION_BUY, Holding.ACTION_NEW]
        ).order_by("-share_change")[:20]

        return HoldingSerializer(holdings, many=True).data

    def get_decreased_positions(self, obj):
        """获取减仓持仓"""
        latest = self.get_latest_filing(obj)
        if not latest:
            return []

        holdings = latest.holdings.filter(action_type=Holding.ACTION_SELL).order_by(
            "share_change"
        )[:20]

        return HoldingSerializer(holdings, many=True).data

    def get_call_options(self, obj):
        """获取看涨期权"""
        latest = self.get_latest_filing(obj)
        if not latest:
            return []

        options = latest.option_positions.filter(
            option_type=OptionPosition.OPTION_CALL
        ).order_by("-notional_value")[:20]

        return OptionPositionSerializer(options, many=True).data

    def get_put_options(self, obj):
        """获取看跌期权"""
        latest = self.get_latest_filing(obj)
        if not latest:
            return []

        options = latest.option_positions.filter(
            option_type=OptionPosition.OPTION_PUT
        ).order_by("-notional_value")[:20]

        return OptionPositionSerializer(options, many=True).data


class CrawlLogSerializer(serializers.ModelSerializer):
    """
    爬虫日志序列化器 (Crawl Log Serializer)
    """

    class Meta:
        model = CrawlLog
        fields = [
            "id",
            "status",
            "filings_processed",
            "error_message",
            "task_id",
            "timestamp",
        ]


class DashboardSummarySerializer(serializers.Serializer):
    """
    仪表盘摘要序列化器 (Dashboard Summary Serializer)

    用于/api/dashboard/summary端点
    """

    top_picks_cards = serializers.ListField()
    recent_activity = serializers.ListField()


class MonitoredCompanySerializer(serializers.Serializer):
    """
    监控公司序列化器 (Monitored Company Serializer)

    用于设置页面
    """

    id = serializers.UUIDField()
    cik = serializers.CharField()
    name = serializers.CharField()
    is_active = serializers.BooleanField()
    last_update = serializers.DateTimeField(required=False)


class SystemStatusSerializer(serializers.Serializer):
    """
    系统状态序列化器 (System Status Serializer)
    """

    success_count = serializers.IntegerField()
    error_count = serializers.IntegerField()
    last_crawl_time = serializers.DateTimeField(required=False, allow_null=True)
    total_institutions = serializers.IntegerField()
    total_filings = serializers.IntegerField()
