"""
Django Admin configuration for crawler models.
爬虫模型的Django管理后台配置
"""

from django.contrib import admin
from .models import Institution, Filing, Holding, OptionPosition, CrawlLog


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    """
    机构管理界面 (Institution Admin Interface)
    """

    list_display = ("name", "cik", "avatar_initials", "aum", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "cik")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        ("基本信息", {"fields": ("id", "cik", "name", "avatar_initials")}),
        ("财务信息", {"fields": ("aum",)}),
        ("状态", {"fields": ("is_active", "created_at", "updated_at")}),
    )


@admin.register(Filing)
class FilingAdmin(admin.ModelAdmin):
    """
    申报文件管理界面 (Filing Admin Interface)
    """

    list_display = (
        "institution",
        "quarter",
        "period_of_report",
        "filing_date",
        "accession_number",
    )
    list_filter = ("period_of_report", "filing_date")
    search_fields = ("institution__name", "accession_number", "quarter")
    readonly_fields = ("id", "created_at")
    date_hierarchy = "period_of_report"

    def get_queryset(self, request):
        """优化查询，减少数据库访问"""
        qs = super().get_queryset(request)
        return qs.select_related("institution")


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    """
    持仓明细管理界面 (Holding Admin Interface)
    """

    list_display = (
        "ticker",
        "company_name",
        "share_count",
        "value",
        "action_type",
        "pct_change",
    )
    list_filter = ("action_type", "filing__period_of_report")
    search_fields = ("ticker", "company_name", "cusip")
    readonly_fields = ("id", "created_at")

    def get_queryset(self, request):
        """优化查询"""
        qs = super().get_queryset(request)
        return qs.select_related("filing", "filing__institution")


@admin.register(OptionPosition)
class OptionPositionAdmin(admin.ModelAdmin):
    """
    期权持仓管理界面 (Option Position Admin Interface)
    """

    list_display = (
        "ticker",
        "option_type",
        "contracts",
        "notional_value",
        "get_institution",
    )
    list_filter = ("option_type", "filing__period_of_report")
    search_fields = ("ticker",)
    readonly_fields = ("id", "created_at")

    def get_institution(self, obj):
        """获取所属机构名称"""
        return obj.filing.institution.name

    get_institution.short_description = "机构"

    def get_queryset(self, request):
        """优化查询"""
        qs = super().get_queryset(request)
        return qs.select_related("filing", "filing__institution")


@admin.register(CrawlLog)
class CrawlLogAdmin(admin.ModelAdmin):
    """
    爬虫日志管理界面 (Crawl Log Admin Interface)
    """

    list_display = (
        "timestamp",
        "status",
        "filings_processed",
        "task_id",
        "get_error_preview",
    )
    list_filter = ("status", "timestamp")
    search_fields = ("task_id", "error_message")
    readonly_fields = ("id", "timestamp")
    date_hierarchy = "timestamp"

    def get_error_preview(self, obj):
        """显示错误信息预览"""
        if obj.error_message:
            return (
                obj.error_message[:100] + "..."
                if len(obj.error_message) > 100
                else obj.error_message
            )
        return "-"

    get_error_preview.short_description = "错误信息"

    def has_add_permission(self, request):
        """禁止手动添加日志"""
        return False
