"""
Database models for 13F Tracker application.
13F追踪系统的数据库模型

This module defines all database models according to the integration specification:
- Institution (机构表)
- Filing (申报文件表)
- Holding (持仓明细表)
- OptionPosition (期权持仓表)
- CrawlLog (爬虫日志表)
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Institution(models.Model):
    """
    机构表 (Institution Table)

    存储被监控的机构投资者信息
    Stores information about monitored institutional investors
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="机构ID"
    )
    cik = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        verbose_name="CIK编号",
        help_text="SEC Central Index Key，10位数字",
    )
    name = models.CharField(
        max_length=255, verbose_name="机构名称", help_text="例如: Berkshire Hathaway"
    )
    avatar_initials = models.CharField(
        max_length=3,
        blank=True,
        verbose_name="缩写",
        help_text="前端展示用的缩写，例如: BH",
    )
    aum = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="资产管理规模",
        help_text="Assets Under Management (AUM)",
    )
    is_active = models.BooleanField(
        default=True, verbose_name="是否激活", help_text="是否在监控列表中"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "institutions"
        verbose_name = "机构"
        verbose_name_plural = "机构列表"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} (CIK: {self.cik})"

    def save(self, *args, **kwargs):
        """
        保存前自动生成缩写 (Auto-generate initials before saving)
        """
        if not self.avatar_initials and self.name:
            # 提取首字母作为缩写
            words = self.name.split()[:3]
            self.avatar_initials = "".join([w[0].upper() for w in words if w])[:3]
        super().save(*args, **kwargs)


class Filing(models.Model):
    """
    申报文件表 (Filing Table)

    存储13F-HR申报文件的元数据
    Stores metadata for 13F-HR filing documents
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="文件ID"
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="filings",
        db_index=True,
        verbose_name="所属机构",
    )
    period_of_report = models.DateField(
        verbose_name="报告期截止日", help_text="例如: 2024-12-31"
    )
    filing_date = models.DateField(
        verbose_name="实际提交日", help_text="文件提交给SEC的日期"
    )
    accession_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="文件编号",
        help_text="SEC唯一文件编号，用于去重",
    )
    quarter = models.CharField(
        max_length=10, verbose_name="季度", help_text="例如: Q4 2024"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "filings"
        verbose_name = "申报文件"
        verbose_name_plural = "申报文件列表"
        ordering = ["-period_of_report", "-filing_date"]
        indexes = [
            models.Index(fields=["institution", "-period_of_report"]),
            models.Index(fields=["accession_number"]),
        ]

    def __str__(self):
        return f"{self.institution.name} - {self.quarter} ({self.accession_number})"


class Holding(models.Model):
    """
    持仓明细表 (Holding Table)

    存储机构的股票持仓明细及变动信息
    Stores detailed stock holdings and changes for institutions
    """

    # 操作类型选择 (Action type choices)
    ACTION_NEW = "NEW"
    ACTION_BUY = "Buy"
    ACTION_SELL = "Sell"
    ACTION_SOLD_OUT = "Sold Out"
    ACTION_HOLD = "Hold"

    ACTION_CHOICES = [
        (ACTION_NEW, "新建仓"),
        (ACTION_BUY, "加仓"),
        (ACTION_SELL, "减仓"),
        (ACTION_SOLD_OUT, "清仓"),
        (ACTION_HOLD, "持有"),
    ]

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="持仓ID"
    )
    filing = models.ForeignKey(
        Filing,
        on_delete=models.CASCADE,
        related_name="holdings",
        db_index=True,
        verbose_name="所属申报文件",
    )
    ticker = models.CharField(
        max_length=20, db_index=True, verbose_name="股票代码", help_text="例如: AAPL"
    )
    company_name = models.CharField(max_length=255, verbose_name="公司名称")
    cusip = models.CharField(
        max_length=9, verbose_name="CUSIP代码", help_text="9位证券识别码"
    )
    share_count = models.BigIntegerField(
        validators=[MinValueValidator(0)], verbose_name="持股数量"
    )
    value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="市值",
        help_text="单位: 美元",
    )
    pct_portfolio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="仓位占比",
        help_text="占投资组合的百分比",
    )

    # 差异字段 (Diff fields - calculated by backend)
    share_change = models.BigIntegerField(
        null=True, blank=True, verbose_name="股数变动", help_text="较上季度变动股数"
    )
    pct_change = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="变动百分比",
        help_text="较上季度变动百分比",
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        null=True,
        blank=True,
        verbose_name="操作类型",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "holdings"
        verbose_name = "持仓明细"
        verbose_name_plural = "持仓明细列表"
        ordering = ["-value"]
        indexes = [
            models.Index(fields=["filing", "ticker"]),
            models.Index(fields=["ticker"]),
            models.Index(fields=["action_type"]),
        ]

    def __str__(self):
        return f"{self.ticker} - {self.share_count} shares (${self.value})"


class OptionPosition(models.Model):
    """
    期权持仓表 (Option Position Table)

    存储机构的期权持仓信息
    Stores option positions for institutions
    """

    # 期权类型选择 (Option type choices)
    OPTION_CALL = "CALL"
    OPTION_PUT = "PUT"

    OPTION_TYPE_CHOICES = [
        (OPTION_CALL, "看涨期权"),
        (OPTION_PUT, "看跌期权"),
    ]

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="期权ID"
    )
    filing = models.ForeignKey(
        Filing,
        on_delete=models.CASCADE,
        related_name="option_positions",
        db_index=True,
        verbose_name="所属申报文件",
    )
    ticker = models.CharField(max_length=20, verbose_name="股票代码")
    option_type = models.CharField(
        max_length=4, choices=OPTION_TYPE_CHOICES, verbose_name="期权类型"
    )
    contracts = models.BigIntegerField(
        validators=[MinValueValidator(0)], verbose_name="合约数量"
    )
    notional_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="名义价值",
        help_text="单位: 美元",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "option_positions"
        verbose_name = "期权持仓"
        verbose_name_plural = "期权持仓列表"
        ordering = ["-notional_value"]
        indexes = [
            models.Index(fields=["filing", "option_type"]),
            models.Index(fields=["ticker"]),
        ]

    def __str__(self):
        return f"{self.ticker} {self.option_type} - {self.contracts} contracts"


class CrawlLog(models.Model):
    """
    爬虫日志表 (Crawl Log Table)

    记录爬虫执行的历史和状态
    Records crawler execution history and status
    """

    # 状态选择 (Status choices)
    STATUS_SUCCESS = "SUCCESS"
    STATUS_ERROR = "ERROR"
    STATUS_RUNNING = "RUNNING"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "成功"),
        (STATUS_ERROR, "失败"),
        (STATUS_RUNNING, "运行中"),
    ]

    id = models.AutoField(primary_key=True, verbose_name="日志ID")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="状态"
    )
    filings_processed = models.IntegerField(default=0, verbose_name="处理的文件数")
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    task_id = models.CharField(max_length=255, blank=True, verbose_name="Celery任务ID")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="时间戳")

    class Meta:
        db_table = "crawl_logs"
        verbose_name = "爬虫日志"
        verbose_name_plural = "爬虫日志列表"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.status} - {self.timestamp} ({self.filings_processed} filings)"
