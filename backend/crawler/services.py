"""
Service layer for crawler operations.
爬虫操作的服务层

This module contains business logic for:
- CIK lookup and validation
- Filing data processing
- Diff calculation between quarters
- Data persistence to database
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal

from django.db import transaction
from django.conf import settings

from .models import Institution, Filing, Holding, OptionPosition, CrawlLog

logger = logging.getLogger(__name__)


class InstitutionService:
    """
    机构服务类 (Institution Service)

    处理机构的查找、验证和管理
    Handles institution lookup, validation, and management
    """

    def __init__(self):
        """初始化服务，加载CIK缓存"""
        self.ticker_cik_cache = self._load_ticker_cik_cache()

    def _load_ticker_cik_cache(self) -> Dict[str, str]:
        """
        加载ticker到CIK的映射缓存
        Load ticker to CIK mapping cache
        """
        cache_file = Path(__file__).parent / "ticker_cik_cache.json"

        try:
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                logger.info(f"✅ 加载了 {len(cache)} 个ticker-CIK映射")
                return cache
            else:
                logger.warning("⚠️ ticker_cik_cache.json 文件不存在")
                return {}
        except Exception as e:
            logger.error(f"❌ 加载ticker_cik_cache.json失败: {e}")
            return {}

    def lookup_cik(self, identifier: str) -> Optional[str]:
        """
        查找CIK编号
        Lookup CIK number by ticker or CIK

        Args:
            identifier: Ticker symbol or CIK number

        Returns:
            CIK number (10 digits, zero-padded) or None
        """
        identifier = identifier.strip().upper()

        # 如果已经是CIK格式（纯数字）
        if identifier.isdigit():
            return identifier.zfill(10)

        # 从缓存中查找ticker
        if identifier in self.ticker_cik_cache:
            cik = self.ticker_cik_cache[identifier]
            return cik.zfill(10)

        logger.warning(f"⚠️ 未找到 {identifier} 的CIK映射")
        return None

    def get_or_create_institution(
        self, cik: str, name: Optional[str] = None
    ) -> Institution:
        """
        获取或创建机构记录
        Get or create institution record

        Args:
            cik: CIK number
            name: Institution name (optional)

        Returns:
            Institution instance
        """
        cik = cik.zfill(10)  # 确保10位数字

        institution, created = Institution.objects.get_or_create(
            cik=cik, defaults={"name": name or f"Institution {cik}", "is_active": True}
        )

        if created:
            logger.info(f"✅ 创建新机构: {institution.name} (CIK: {cik})")

        # 如果提供了名称且与现有名称不同，更新名称
        if name and institution.name != name:
            institution.name = name
            institution.save(update_fields=["name"])
            logger.info(f"📝 更新机构名称: {name}")

        return institution


class FilingService:
    """
    申报文件服务类 (Filing Service)

    处理13F文件的解析、存储和差异计算
    Handles 13F filing parsing, storage, and diff calculation
    """

    def __init__(self):
        self.institution_service = InstitutionService()

    def check_filing_exists(self, accession_number: str) -> bool:
        """
        检查文件是否已存在（幂等性检查）
        Check if filing already exists (idempotency check)

        Args:
            accession_number: SEC accession number

        Returns:
            True if exists, False otherwise
        """
        return Filing.objects.filter(accession_number=accession_number).exists()

    def save_filing_data(
        self,
        institution: Institution,
        filing_data: Dict[str, Any],
        holdings_data: List[Dict[str, Any]],
        accession_number: str,
    ) -> Filing:
        """
        保存申报文件及持仓数据到数据库
        Save filing and holdings data to database

        Args:
            institution: Institution instance
            filing_data: Filing metadata
            holdings_data: List of holdings
            accession_number: SEC accession number

        Returns:
            Created Filing instance
        """
        logger.info(f"💾 开始保存 {institution.name} 的申报数据...")

        try:
            with transaction.atomic():
                # 1. 创建Filing记录
                filing = self._create_filing(institution, filing_data, accession_number)

                # 2. 分流Holding和OptionPosition
                holdings_list = []
                options_list = []

                for item in holdings_data:
                    if item.get("put_call") in ["PUT", "CALL"]:
                        # 期权持仓
                        options_list.append(self._create_option_position(filing, item))
                    else:
                        # 普通股票持仓
                        holdings_list.append(self._create_holding(filing, item))

                # 3. 批量入库（SQLite性能优化）
                if holdings_list:
                    Holding.objects.bulk_create(holdings_list)
                    logger.info(f"✅ 保存了 {len(holdings_list)} 个股票持仓")

                if options_list:
                    OptionPosition.objects.bulk_create(options_list)
                    logger.info(f"✅ 保存了 {len(options_list)} 个期权持仓")

                # 4. 计算差异（与上一季度对比）
                self._calculate_and_update_diffs(filing)

                logger.info(f"🎉 成功保存申报文件: {filing.quarter}")
                return filing

        except Exception as e:
            logger.error(f"❌ 保存申报数据失败: {e}")
            raise

    def _create_filing(
        self,
        institution: Institution,
        filing_data: Dict[str, Any],
        accession_number: str,
    ) -> Filing:
        """创建Filing记录"""
        # 解析日期
        period_of_report = self._parse_date(filing_data.get("period_of_report"))
        filing_date = self._parse_date(filing_data.get("filing_date"))

        # 生成季度标识
        quarter = self._generate_quarter_label(period_of_report)

        filing = Filing.objects.create(
            institution=institution,
            period_of_report=period_of_report,
            filing_date=filing_date,
            accession_number=accession_number,
            quarter=quarter,
        )

        return filing

    def _create_holding(self, filing: Filing, item: Dict[str, Any]) -> Holding:
        """创建Holding对象"""
        # 提取股票代码（从issuer_name或title_of_class中推断）
        ticker = self._extract_ticker(item)

        return Holding(
            filing=filing,
            ticker=ticker,
            company_name=item.get("issuer_name", "")[:255],
            cusip=item.get("cusip", ""),
            share_count=int(item.get("shares_or_principal", {}).get("amount", 0) or 0),
            value=Decimal(str(item.get("value_usd", 0) or 0)),
            pct_portfolio=None,  # 稍后计算
        )

    def _create_option_position(
        self, filing: Filing, item: Dict[str, Any]
    ) -> OptionPosition:
        """创建OptionPosition对象"""
        ticker = self._extract_ticker(item)

        # 期权的合约数量 = 股数 / 100（标准期权合约）
        shares = int(item.get("shares_or_principal", {}).get("amount", 0) or 0)
        contracts = shares // 100 if shares > 0 else 0

        return OptionPosition(
            filing=filing,
            ticker=ticker,
            option_type=item.get("put_call", "CALL"),
            contracts=contracts,
            notional_value=Decimal(str(item.get("value_usd", 0) or 0)),
        )

    def _extract_ticker(self, item: Dict[str, Any]) -> str:
        """
        从持仓数据中提取股票代码
        Extract ticker symbol from holding data

        优先级：
        1. title_of_class中的代码（如 "COM" -> 需要通过CUSIP查找）
        2. issuer_name（公司名称）
        3. CUSIP反查
        """
        # 简化版本：直接使用CUSIP作为ticker（后续可以通过yfinance等工具优化）
        cusip = item.get("cusip", "")
        if cusip:
            return cusip[:6]  # 使用CUSIP前6位作为临时ticker

        return "UNKNOWN"

    def _calculate_and_update_diffs(self, current_filing: Filing):
        """
        计算并更新持仓差异
        Calculate and update holding differences

        按照集成文档4.2节的差异计算引擎实现
        """
        logger.info(f"🔄 开始计算 {current_filing.quarter} 的持仓差异...")

        # 查找上一季度的Filing
        previous_filing = (
            Filing.objects.filter(
                institution=current_filing.institution,
                period_of_report__lt=current_filing.period_of_report,
            )
            .order_by("-period_of_report")
            .first()
        )

        if not previous_filing:
            logger.info("ℹ️ 没有上一季度数据，所有持仓标记为NEW")
            # 所有持仓标记为NEW
            Holding.objects.filter(filing=current_filing).update(
                action_type=Holding.ACTION_NEW, share_change=0, pct_change=None
            )
            return

        # 获取当前和上一季度的持仓
        current_holdings = {
            h.ticker: h for h in Holding.objects.filter(filing=current_filing)
        }
        previous_holdings = {
            h.ticker: h for h in Holding.objects.filter(filing=previous_filing)
        }

        current_tickers = set(current_holdings.keys())
        previous_tickers = set(previous_holdings.keys())

        # 1. 新建仓 (NEW)
        new_tickers = current_tickers - previous_tickers
        for ticker in new_tickers:
            holding = current_holdings[ticker]
            holding.action_type = Holding.ACTION_NEW
            holding.share_change = holding.share_count
            holding.pct_change = None
            holding.save(update_fields=["action_type", "share_change", "pct_change"])

        # 2. 清仓 (Sold Out)
        sold_out_tickers = previous_tickers - current_tickers
        for ticker in sold_out_tickers:
            prev_holding = previous_holdings[ticker]
            # 创建一个share_count=0的记录表示清仓
            Holding.objects.create(
                filing=current_filing,
                ticker=ticker,
                company_name=prev_holding.company_name,
                cusip=prev_holding.cusip,
                share_count=0,
                value=Decimal("0"),
                action_type=Holding.ACTION_SOLD_OUT,
                share_change=-prev_holding.share_count,
                pct_change=Decimal("-100.00"),
            )

        # 3. 持续持有 (Buy/Sell/Hold)
        continuing_tickers = current_tickers & previous_tickers
        for ticker in continuing_tickers:
            current = current_holdings[ticker]
            previous = previous_holdings[ticker]

            share_change = current.share_count - previous.share_count

            if previous.share_count > 0:
                pct_change = Decimal(str((share_change / previous.share_count) * 100))
            else:
                pct_change = None

            # 判断操作类型
            if share_change > 0:
                action_type = Holding.ACTION_BUY
            elif share_change < 0:
                action_type = Holding.ACTION_SELL
            else:
                action_type = Holding.ACTION_HOLD

            current.action_type = action_type
            current.share_change = share_change
            current.pct_change = pct_change
            current.save(update_fields=["action_type", "share_change", "pct_change"])

        logger.info(
            f"✅ 差异计算完成: "
            f"新建仓={len(new_tickers)}, "
            f"清仓={len(sold_out_tickers)}, "
            f"持续持有={len(continuing_tickers)}"
        )

    def _parse_date(self, date_str: Any) -> date:
        """解析日期字符串"""
        if isinstance(date_str, date):
            return date_str

        if isinstance(date_str, str):
            # 尝试多种日期格式
            for fmt in ["%Y-%m-%d", "%Y%m%d", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue

        # 默认返回今天
        return datetime.now().date()

    def _generate_quarter_label(self, report_date: date) -> str:
        """
        生成季度标签
        Generate quarter label (e.g., "Q4 2024")
        """
        quarter = (report_date.month - 1) // 3 + 1
        return f"Q{quarter} {report_date.year}"


class CrawlLogService:
    """
    爬虫日志服务类 (Crawl Log Service)

    管理爬虫执行日志
    Manages crawler execution logs
    """

    @staticmethod
    def create_log(
        status: str,
        filings_processed: int = 0,
        error_message: str = "",
        task_id: str = "",
    ) -> CrawlLog:
        """
        创建爬虫日志
        Create crawl log entry
        """
        return CrawlLog.objects.create(
            status=status,
            filings_processed=filings_processed,
            error_message=error_message,
            task_id=task_id,
        )

    @staticmethod
    def get_statistics() -> Dict[str, int]:
        """
        获取爬虫统计信息
        Get crawler statistics
        """
        success_count = CrawlLog.objects.filter(status=CrawlLog.STATUS_SUCCESS).count()
        error_count = CrawlLog.objects.filter(status=CrawlLog.STATUS_ERROR).count()

        return {"success_count": success_count, "error_count": error_count}
