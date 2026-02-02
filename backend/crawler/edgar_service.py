"""
EDGAR Crawler Service for Django Integration
EDGAR爬虫服务的Django集成

This service wraps the EDGAR downloader functionality for use with Django models.
此服务封装EDGAR下载器功能以便与Django模型配合使用。
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal

import requests
from django.conf import settings
from django.db import transaction

from .models import Institution, Filing, Holding, OptionPosition
from .sec_13f_extractor import SEC13FExtractor
from .services import FilingService

logger = logging.getLogger(__name__)


class EDGARCrawlerService:
    """
    EDGAR爬虫服务类 (EDGAR Crawler Service)

    封装SEC EDGAR API交互和数据下载逻辑
    Encapsulates SEC EDGAR API interaction and data download logic
    """

    # SEC EDGAR API基础URL
    SEC_EDGAR_API_BASE = "https://data.sec.gov"
    SEC_EDGAR_ARCHIVES_BASE = "https://www.sec.gov/cgi-bin/browse-edgar"

    def __init__(self):
        """初始化爬虫服务"""
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": settings.SEC_USER_AGENT,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov",
            }
        )
        self.extractor = SEC13FExtractor()
        self.filing_service = FilingService()
        self.request_delay = settings.SEC_REQUEST_DELAY

    def crawl_institution_13f(
        self, institution: Institution, max_filings: int = 4
    ) -> int:
        """
        爬取机构的13F-HR文件
        Crawl 13F-HR filings for an institution

        Args:
            institution: Institution instance
            max_filings: Maximum number of filings to fetch

        Returns:
            Number of filings processed
        """
        logger.info(f"🔍 开始爬取机构: {institution.name} (CIK: {institution.cik})")

        try:
            # 1. 获取13F-HR文件列表
            filings_list = self._get_13f_filings_list(institution.cik, max_filings)

            if not filings_list:
                logger.warning(f"⚠️ 未找到 {institution.name} 的13F-HR文件")
                return 0

            logger.info(f"📋 找到 {len(filings_list)} 个13F-HR文件")

            # 2. 处理每个文件
            processed_count = 0
            for filing_info in filings_list:
                try:
                    # 检查是否已存在
                    accession_number = filing_info["accession_number"]
                    if self.filing_service.check_filing_exists(accession_number):
                        logger.info(f"⏭️ 文件已存在，跳过: {accession_number}")
                        continue

                    # 下载并处理文件
                    success = self._download_and_process_13f(institution, filing_info)

                    if success:
                        processed_count += 1
                        logger.info(
                            f"✅ 成功处理文件 {processed_count}/{len(filings_list)}"
                        )

                    # SEC要求：每次请求之间延迟
                    time.sleep(self.request_delay)

                except Exception as e:
                    logger.error(f"❌ 处理文件失败: {e}")
                    continue

            logger.info(
                f"🎉 完成爬取 {institution.name}，处理了 {processed_count} 个文件"
            )
            return processed_count

        except Exception as e:
            logger.error(f"❌ 爬取机构失败: {e}")
            raise

    def _get_13f_filings_list(
        self, cik: str, max_count: int = 4
    ) -> List[Dict[str, Any]]:
        """
        获取13F-HR文件列表
        Get list of 13F-HR filings

        Args:
            cik: CIK number (10 digits)
            max_count: Maximum number of filings to return

        Returns:
            List of filing information dictionaries
        """
        # SEC API使用10位数字的CIK（带前导零）
        cik_padded = cik.zfill(10)

        # 使用SEC的submissions API
        url = f"{self.SEC_EDGAR_API_BASE}/submissions/CIK{cik_padded}.json"

        try:
            logger.info(f"📡 请求SEC API: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 提取13F-HR文件
            filings = []
            recent_filings = data.get("filings", {}).get("recent", {})

            if not recent_filings:
                return filings

            # 遍历所有文件，筛选13F-HR
            form_types = recent_filings.get("form", [])
            accession_numbers = recent_filings.get("accessionNumber", [])
            filing_dates = recent_filings.get("filingDate", [])
            report_dates = recent_filings.get("reportDate", [])

            for i, form_type in enumerate(form_types):
                if form_type == "13F-HR" and len(filings) < max_count:
                    filings.append(
                        {
                            "form_type": form_type,
                            "accession_number": accession_numbers[i],
                            "filing_date": filing_dates[i],
                            "report_date": (
                                report_dates[i]
                                if i < len(report_dates)
                                else filing_dates[i]
                            ),
                            "primary_document": self._get_primary_document_name(
                                accession_numbers[i]
                            ),
                        }
                    )

            return filings

        except requests.RequestException as e:
            logger.error(f"❌ SEC API请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ 解析SEC数据失败: {e}")
            return []

    def _get_primary_document_name(self, accession_number: str) -> str:
        """
        获取主文档名称
        Get primary document name

        13F-HR的主文档通常是 form13fInfoTable.xml
        """
        return "form13fInfoTable.xml"

    def _download_and_process_13f(
        self, institution: Institution, filing_info: Dict[str, Any]
    ) -> bool:
        """
        下载并处理13F文件
        Download and process 13F filing

        Args:
            institution: Institution instance
            filing_info: Filing information dictionary

        Returns:
            True if successful, False otherwise
        """
        accession_number = filing_info["accession_number"]
        logger.info(f"📥 下载文件: {accession_number}")

        try:
            # 1. 下载信息表XML
            xml_content = self._download_information_table(
                institution.cik, accession_number
            )

            if not xml_content:
                logger.error(f"❌ 下载信息表失败: {accession_number}")
                return False

            # 2. 提取持仓数据
            extracted_data = self.extractor.extract_13f_data(
                xml_content, source_file=accession_number
            )

            if not extracted_data or not extracted_data.get("holdings"):
                logger.warning(f"⚠️ 未提取到持仓数据: {accession_number}")
                return False

            # 3. 保存到数据库
            filing_metadata = {
                "period_of_report": filing_info["report_date"],
                "filing_date": filing_info["filing_date"],
            }

            filing = self.filing_service.save_filing_data(
                institution=institution,
                filing_data=filing_metadata,
                holdings_data=extracted_data["holdings"],
                accession_number=accession_number,
            )

            logger.info(f"💾 成功保存文件: {filing.quarter}")
            return True

        except Exception as e:
            logger.error(f"❌ 下载和处理文件失败: {e}")
            return False

    def _download_information_table(
        self, cik: str, accession_number: str
    ) -> Optional[str]:
        """
        下载13F信息表XML
        Download 13F information table XML

        Args:
            cik: CIK number
            accession_number: Accession number (e.g., "0001193125-21-000001")

        Returns:
            XML content as string, or None if failed
        """
        # 格式化accession number（移除破折号）
        accession_no_dash = accession_number.replace("-", "")
        cik_no_zeros = cik.lstrip("0")

        # 尝试多种可能的XML文件名
        possible_filenames = [
            "form13fInfoTable.xml",
            "primary_doc.xml",
            "form13f_infoTable.xml",
            "infotable.xml",
            f"{accession_no_dash}.xml",
        ]

        for filename in possible_filenames:
            url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik_no_zeros}/{accession_no_dash}/{filename}"
            )

            try:
                logger.info(f"📡 尝试下载: {filename}")
                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    # 验证是否是XML内容
                    if "<?xml" in response.text or "<informationTable" in response.text:
                        logger.info(f"✅ 成功下载XML: {filename}")
                        return response.text

            except requests.RequestException:
                continue

        # 如果所有尝试都失败，尝试获取文件列表
        logger.warning(f"⚠️ 未找到标准XML文件，尝试获取文件列表...")

        try:
            # 获取该申报的所有文件列表
            index_url = (
                f"https://www.sec.gov/cgi-bin/viewer?"
                f"action=view&cik={cik}&accession_number={accession_number}&"
                f"xbrl_type=v"
            )

            logger.info(f"📡 获取文件列表: {index_url}")
            response = self.session.get(index_url, timeout=30)

            if response.status_code == 200 and "xml" in response.text.lower():
                # 简单解析，查找XML文件链接
                import re

                xml_files = re.findall(r'href="([^"]*\.xml)"', response.text, re.I)

                if xml_files:
                    # 尝试第一个XML文件
                    xml_url = (
                        f"https://www.sec.gov{xml_files[0]}"
                        if xml_files[0].startswith("/")
                        else xml_files[0]
                    )
                    logger.info(f"📡 尝试下载找到的XML: {xml_url}")

                    xml_response = self.session.get(xml_url, timeout=30)
                    if xml_response.status_code == 200:
                        return xml_response.text

        except Exception as e:
            logger.error(f"❌ 获取文件列表失败: {e}")

        return None

    def get_latest_filing_date(self, institution: Institution) -> Optional[date]:
        """
        获取机构最新的申报日期
        Get latest filing date for institution

        Args:
            institution: Institution instance

        Returns:
            Latest filing date or None
        """
        latest_filing = institution.filings.order_by("-period_of_report").first()
        return latest_filing.period_of_report if latest_filing else None

    def should_update(self, institution: Institution) -> bool:
        """
        判断是否需要更新
        Determine if institution needs update

        Args:
            institution: Institution instance

        Returns:
            True if update needed, False otherwise
        """
        latest_date = self.get_latest_filing_date(institution)

        if not latest_date:
            return True  # 没有数据，需要更新

        # 如果最新数据超过90天，需要更新
        days_old = (date.today() - latest_date).days
        return days_old > 90
