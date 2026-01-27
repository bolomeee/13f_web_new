#!/usr/bin/env python3
"""
SEC 13F持仓数据提取器 (SEC 13F Holdings Extractor)

专门用于解析和提取13F-HR表单中的机构投资者持仓数据。
13F表单使用XML格式（非XBRL），包含详细的持仓明细信息。

功能特点:
- 解析informationtable.xml文件
- 提取完整的持仓明细（发行人、CUSIP、市值、股数等）
- 处理投票权和投资决策权信息
- 生成结构化的JSON输出
- 支持数据验证和统计分析

作者: EDGAR Downloader Team
版本: 1.0
"""

import logging
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SEC13FExtractor:
    """SEC 13F持仓数据提取器 - 专门处理XML格式的13F-HR表单"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 13F XML可能使用的命名空间
        self.namespaces = {
            "ns1": "http://www.sec.gov/edgar/document/thirteenf/informationtable",
            "": "",  # 默认命名空间
        }

    def extract_13f_data(
        self, xml_content: str, source_file: str = ""
    ) -> Dict[str, Any]:
        """
        从13F XML文件中提取完整的持仓数据

        Args:
            xml_content: XML文档内容
            source_file: 源文件路径

        Returns:
            Dict: 包含元数据、持仓明细和统计信息的结构化数据
        """

        self.logger.info("🔍 开始解析13F持仓数据...")

        try:
            # 尝试解析XML
            root = self._parse_xml(xml_content)

            if root is None:
                self.logger.error("❌ XML解析失败")
                return self._create_empty_result(source_file)

            # 提取文档元数据
            metadata = self._extract_metadata(root, source_file)

            # 提取持仓明细
            holdings = self._extract_holdings(root)

            # 计算统计信息
            statistics = self._calculate_statistics(holdings, metadata)

            self.logger.info(f"✅ 成功提取 {len(holdings)} 个持仓记录")

            return {
                "document_metadata": metadata,
                "holdings": holdings,
                "summary_statistics": statistics,
                "extraction_info": {
                    "source_file": source_file,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "total_holdings": len(holdings),
                    "extraction_method": "xml_parser",
                },
            }

        except Exception as e:
            self.logger.error(f"❌ 提取13F数据时出错: {e}")
            return self._create_empty_result(source_file, str(e))

    def _parse_xml(self, xml_content: str) -> Optional[ET.Element]:
        """解析XML内容，处理可能的编码和格式问题"""

        try:
            # 清理XML内容
            xml_content = xml_content.strip()

            # 移除BOM标记（如果存在）
            if xml_content.startswith("\ufeff"):
                xml_content = xml_content[1:]

            # 处理以<XML>标签开头的内容（SEC EDGAR格式）
            if xml_content.upper().startswith("<XML>"):
                # 移除开头的<XML>标签
                xml_content = re.sub(r"^<XML>\s*", "", xml_content, flags=re.IGNORECASE)
                # 移除结尾的</XML>标签
                xml_content = re.sub(
                    r"\s*</XML>\s*$", "", xml_content, flags=re.IGNORECASE
                )
                xml_content = xml_content.strip()

            # 尝试直接解析
            root = ET.fromstring(xml_content)
            return root

        except ET.ParseError as e:
            self.logger.warning(f"⚠️ XML解析错误，尝试修复: {e}")

            # 尝试使用BeautifulSoup修复格式问题
            try:
                soup = BeautifulSoup(xml_content, "xml")
                cleaned_xml = str(soup)
                root = ET.fromstring(cleaned_xml)
                return root
            except Exception as e2:
                self.logger.error(f"❌ XML修复失败: {e2}")
                return None

    def _extract_metadata(self, root: ET.Element, source_file: str) -> Dict[str, Any]:
        """提取13F文档的元数据"""

        metadata = {
            "form_type": "13F-HR",
            "filing_manager": "Unknown",
            "report_period": "Unknown",
            "cik": "Unknown",
            "file_number": "Unknown",
            "source_file": source_file,
        }

        try:
            # 从文件名中提取信息
            if source_file:
                # 文件名格式: TICKER_CIK_XXXXX_FORM_13F-HR_YYYY-MM-DD.xml
                filename_pattern = r"([A-Z]+)_CIK_(\d+)_FORM_13F-HR_(\d{4}-\d{2}-\d{2})"
                match = re.search(filename_pattern, source_file)

                if match:
                    metadata["ticker"] = match.group(1)
                    metadata["cik"] = match.group(2)
                    metadata["filing_date"] = match.group(3)

            # 从XML中提取报告期信息
            # 13F的报告期通常在coverPage或formData中
            cover_page = root.find(".//coverPage") or root.find(
                ".//ns1:coverPage", self.namespaces
            )
            if cover_page is not None:
                report_period = cover_page.findtext(
                    ".//reportCalendarOrQuarter"
                ) or cover_page.findtext(
                    ".//ns1:reportCalendarOrQuarter", self.namespaces
                )
                if report_period:
                    metadata["report_period"] = report_period.strip()

                filing_manager = cover_page.findtext(
                    ".//filingManager/name"
                ) or cover_page.findtext(
                    ".//ns1:filingManager/ns1:name", self.namespaces
                )
                if filing_manager:
                    metadata["filing_manager"] = filing_manager.strip()

        except Exception as e:
            self.logger.warning(f"⚠️ 提取元数据时出错: {e}")

        return metadata

    def _extract_holdings(self, root: ET.Element) -> List[Dict[str, Any]]:
        """提取所有持仓明细"""

        holdings = []

        try:
            # 13F信息表的标准结构
            # <informationTable><infoTable>...</infoTable></informationTable>

            # 尝试多种可能的路径
            info_tables = (
                root.findall(".//infoTable")
                or root.findall(".//ns1:infoTable", self.namespaces)
                or root.findall(".//informationTable/infoTable")
                or []
            )

            self.logger.info(f"📊 找到 {len(info_tables)} 个持仓记录")

            for idx, info_table in enumerate(info_tables):
                try:
                    holding = self._parse_single_holding(info_table, idx)
                    if holding:
                        holdings.append(holding)
                except Exception as e:
                    self.logger.warning(f"⚠️ 解析第 {idx+1} 个持仓时出错: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"❌ 提取持仓明细时出错: {e}")

        return holdings

    def _parse_single_holding(
        self, info_table: ET.Element, index: int
    ) -> Optional[Dict[str, Any]]:
        """解析单个持仓记录"""

        def get_text(element, tag_name, default=""):
            """安全地获取元素文本"""
            elem = element.find(f".//{tag_name}")
            if elem is None:
                elem = element.find(f".//ns1:{tag_name}", self.namespaces)
            return elem.text.strip() if elem is not None and elem.text else default

        try:
            # 获取原始 value 值 (2023年前是千美元，2023年后是美元)
            raw_value = self._parse_number(get_text(info_table, "value"))

            holding = {
                "position_id": index + 1,
                "issuer_name": get_text(info_table, "nameOfIssuer"),
                "title_of_class": get_text(info_table, "titleOfClass"),
                "cusip": get_text(info_table, "cusip"),
                "value_usd": raw_value,  # 现在直接存储美元值（2023年后数据）
                "value_raw": raw_value,  # 保留原始值用于向后兼容
                "shares_or_principal": {},
                "put_call": get_text(info_table, "putCall"),
                "investment_discretion": get_text(info_table, "investmentDiscretion"),
                "voting_authority": {},
            }

            # 提取股数/本金金额信息
            shrs_or_prn_amt = info_table.find(".//shrsOrPrnAmt") or info_table.find(
                ".//ns1:shrsOrPrnAmt", self.namespaces
            )

            if shrs_or_prn_amt is not None:
                holding["shares_or_principal"] = {
                    "amount": self._parse_number(
                        get_text(shrs_or_prn_amt, "sshPrnamt")
                    ),
                    "type": get_text(shrs_or_prn_amt, "sshPrnamtType"),
                }

            # 提取投票权信息
            voting_authority = info_table.find(".//votingAuthority") or info_table.find(
                ".//ns1:votingAuthority", self.namespaces
            )

            if voting_authority is not None:
                holding["voting_authority"] = {
                    "sole": self._parse_number(get_text(voting_authority, "Sole")),
                    "shared": self._parse_number(get_text(voting_authority, "Shared")),
                    "none": self._parse_number(get_text(voting_authority, "None")),
                }

            # 数据验证
            if not holding["cusip"] or len(holding["cusip"]) != 9:
                self.logger.debug(f"⚠️ 无效的CUSIP: {holding['cusip']}")

            # 计算派生字段 - 估算每股价格
            # 注意：2023年1月3日后 value 字段已经是美元，不需要乘以1000
            if holding["value_usd"] and holding["shares_or_principal"].get("amount"):
                shares = holding["shares_or_principal"]["amount"]
                value_usd = holding["value_usd"]  # 直接使用美元值
                if shares > 0:
                    holding["price_per_share_estimated"] = round(value_usd / shares, 2)

            return holding

        except Exception as e:
            self.logger.warning(f"⚠️ 解析持仓记录时出错: {e}")
            return None

    def _parse_number(self, value_str: str) -> Optional[float]:
        """安全地解析数字字符串"""

        if not value_str:
            return None

        try:
            # 移除逗号和空格
            cleaned = value_str.replace(",", "").replace(" ", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _calculate_statistics(
        self, holdings: List[Dict], metadata: Dict
    ) -> Dict[str, Any]:
        """计算持仓统计信息"""

        if not holdings:
            return {
                "total_positions": 0,
                "total_value_usd": 0,
            }

        # 2023年后 value 字段已经是美元，所以直接使用 value_usd
        total_value = sum(h.get("value_usd", 0) or 0 for h in holdings)
        total_shares = sum(
            h.get("shares_or_principal", {}).get("amount", 0) or 0 for h in holdings
        )

        # 按市值排序，找出前10大持仓
        sorted_holdings = sorted(
            holdings, key=lambda x: x.get("value_usd", 0) or 0, reverse=True
        )

        top_10 = sorted_holdings[:10]
        top_10_summary = [
            {
                "rank": i + 1,
                "issuer": h.get("issuer_name"),
                "cusip": h.get("cusip"),
                "value_usd": h.get("value_usd"),
                "percentage": (
                    round((h.get("value_usd", 0) or 0) / total_value * 100, 2)
                    if total_value > 0
                    else 0
                ),
            }
            for i, h in enumerate(top_10)
        ]

        # 投资决策权分布
        discretion_counts = {}
        for h in holdings:
            discretion = h.get("investment_discretion", "Unknown")
            discretion_counts[discretion] = discretion_counts.get(discretion, 0) + 1

        return {
            "total_positions": len(holdings),
            "total_value_usd": round(total_value, 2),
            "total_shares": round(total_shares, 2),
            "average_position_value_usd": (
                round(total_value / len(holdings), 2) if holdings else 0
            ),
            "top_10_holdings": top_10_summary,
            "investment_discretion_distribution": discretion_counts,
            "report_period": metadata.get("report_period"),
            "filing_manager": metadata.get("filing_manager"),
        }

    def _create_empty_result(
        self, source_file: str, error_message: str = ""
    ) -> Dict[str, Any]:
        """创建空的结果结构"""

        return {
            "document_metadata": {
                "form_type": "13F-HR",
                "source_file": source_file,
                "error": error_message,
            },
            "holdings": [],
            "summary_statistics": {
                "total_positions": 0,
                "total_value_usd": 0,
            },
            "extraction_info": {
                "source_file": source_file,
                "extraction_timestamp": datetime.now().isoformat(),
                "total_holdings": 0,
                "extraction_method": "failed",
                "error": error_message,
            },
        }


def main():
    """测试函数"""

    print("🧪 SEC 13F Extractor 测试模式")
    print("=" * 50)

    # 这里可以添加测试代码
    extractor = SEC13FExtractor()
    print("✅ 13F提取器初始化成功")


if __name__ == "__main__":
    main()
