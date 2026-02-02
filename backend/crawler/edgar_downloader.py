#!/usr/bin/env python3
"""
EDGAR年报下载器和清洗器 (EDGAR Report Downloader & Cleaner)

这是一个完整的SEC文件下载、清洗和结构化处理系统。
支持10-K年报和13F-HR持仓报告。

功能特点:
- 支持批量下载多个公司的10-K年报和13F-HR持仓报告
- 支持指定年份范围（单年或区间）
- 智能解析iXBRL格式的HTML文档（10-K）
- 智能解析XML格式的信息表（13F）
- 按照SEC标准的19个ITEM章节组织内容（10-K）
- 提取完整的持仓明细和投票权信息（13F）
- 自动清理HTML标签和重复文本
- 提取结构化的财务表格和持仓数据
- 输出高质量的JSON格式，适合AI模型分析

作者: EDGAR Downloader Team
版本: 3.0 - 新增13F支持
"""

import json
import re
import os
import time
import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning
from urllib.parse import urljoin
from io import StringIO
import logging
import warnings

# 导入13F提取器
from sec_13f_extractor import SEC13FExtractor

# 过滤BeautifulSoup警告
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("edgar_downloader.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SECStandardExtractor:
    """SEC标准结构提取器 - 严格按照19个ITEM标准组织"""

    # SEC 10-K标准章节结构 (官方19个ITEM)
    STANDARD_ITEMS = {
        "1": "Business",
        "1A": "Risk Factors",
        "1B": "Unresolved Staff Comments",
        "1C": "Cybersecurity",
        "2": "Properties",
        "3": "Legal Proceedings",
        "4": "Mine Safety Disclosures",
        "5": "Market for Registrant Common Equity",
        "6": "Selected Financial Data",
        "7": "Management Discussion and Analysis",
        "7A": "Quantitative and Qualitative Disclosures About Market Risk",
        "8": "Financial Statements and Supplementary Data",
        "9": "Changes in and Disagreements with Accountants",
        "9A": "Controls and Procedures",
        "9B": "Other Information",
        "9C": "Disclosure Regarding Foreign Jurisdictions",
        "10": "Directors, Executive Officers and Corporate Governance",
        "11": "Executive Compensation",
        "12": "Security Ownership of Certain Beneficial Owners",
        "13": "Certain Relationships and Related Transactions",
        "14": "Principal Accountant Fees and Services",
        "15": "Exhibits and Financial Statement Schedules",
        "16": "Form 10-K Summary",
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_sec_sections(
        self, html_content: str, source_file: str
    ) -> Dict[str, Any]:
        """
        按照SEC标准提取19个ITEM章节

        Args:
            html_content: HTML文档内容
            source_file: 源文件路径

        Returns:
            Dict: 包含所有SEC标准章节的结构化数据
        """
        self.logger.info(f"🔍 开始提取SEC标准章节: {source_file}")

        soup = BeautifulSoup(html_content, "lxml")

        # 提取文档元数据
        doc_metadata = self._extract_document_metadata(soup, source_file)

        # 提取SEC标准章节
        sec_sections = self._extract_standard_items(soup)

        # 提取表格数据
        tables = self._extract_structured_tables(soup)

        # 提取XBRL数据
        xbrl_data = self._extract_xbrl_facts(soup)

        # 新增：提取表格中的附注文本并补充到ITEM 8
        table_notes = self._extract_text_from_tables(soup)
        if table_notes:
            item_8_key = "item_8"
            if item_8_key not in sec_sections:
                sec_sections[item_8_key] = {
                    "item_number": "8",
                    "title": "Financial Statements and Supplementary Data",
                    "content": "",
                    "word_count": 0,
                    "char_count": 0,
                    "extraction_method": "table_notes",
                }

            self.logger.info(f"📄 提取到 {len(table_notes)} 条表格附注，补充到ITEM 8")
            cleaned_notes = self._clean_and_merge_content(table_notes)

            # 追加到ITEM 8
            separator = "\n\n--- Table Notes ---\n\n"
            if (
                "content" not in sec_sections[item_8_key]
                or not sec_sections[item_8_key]["content"]
            ):
                sec_sections[item_8_key]["content"] = cleaned_notes
            else:
                sec_sections[item_8_key]["content"] += separator + cleaned_notes

            sec_sections[item_8_key]["char_count"] = len(
                sec_sections[item_8_key]["content"]
            )
            sec_sections[item_8_key]["word_count"] = len(
                sec_sections[item_8_key]["content"].split()
            )

        # 计算处理统计
        processing_stats = self._calculate_processing_stats(
            sec_sections, tables, xbrl_data
        )

        return {
            "document_metadata": doc_metadata,
            "sec_sections": sec_sections,
            "financial_tables": tables,
            "xbrl_data": xbrl_data,
            "processing_stats": processing_stats,
            "extraction_timestamp": datetime.now().isoformat(),
            "extractor_version": "2.2.0",
        }

    def _extract_document_metadata(
        self, soup: BeautifulSoup, source_file: str
    ) -> Dict[str, Any]:
        """提取文档基础元数据 - 修复文件名解析"""

        metadata = {
            "source_file": os.path.basename(source_file),
            "file_size_mb": (
                round(os.path.getsize(source_file) / (1024 * 1024), 2)
                if os.path.exists(source_file)
                else 0
            ),
            "extraction_date": datetime.now().isoformat(),
        }

        # 修复文件名解析逻辑
        filename = os.path.basename(source_file)
        filename_clean = filename.replace(".html", "")

        # 尝试解析标准格式：TICKER_CIK_XXXXXXXX_FORM_10-K_YYYY-MM-DD
        parts = filename_clean.split("_")

        if len(parts) >= 6:
            metadata.update(
                {
                    "ticker": parts[0],
                    "cik": parts[2] if parts[1] == "CIK" else parts[1],
                    "form_type": parts[4] if len(parts) > 4 else "10-K",
                    "filing_date": parts[5] if len(parts) > 5 else None,
                }
            )
        else:
            # 降级解析
            metadata.update(
                {
                    "ticker": parts[0] if parts else "Unknown",
                    "cik": "Unknown",
                    "form_type": "10-K",
                    "filing_date": "Unknown",
                }
            )

        # 从XBRL数据中提取更准确的信息
        try:
            name_elem = soup.find(
                "ix:nonnumeric", {"name": re.compile(r"dei:EntityRegistrantName", re.I)}
            )
            if name_elem:
                metadata["company_name"] = name_elem.get_text().strip()

            cik_elem = soup.find(
                "ix:nonnumeric",
                {"name": re.compile(r"dei:EntityCentralIndexKey", re.I)},
            )
            if cik_elem:
                metadata["cik"] = cik_elem.get_text().strip()

            year_elem = soup.find(
                "ix:nonnumeric",
                {"name": re.compile(r"dei:DocumentFiscalYearFocus", re.I)},
            )
            if year_elem:
                metadata["fiscal_year"] = int(year_elem.get_text().strip())

        except Exception as e:
            self.logger.warning(f"提取XBRL元数据时出错: {e}")

        return metadata

    def _extract_standard_items(self, soup: BeautifulSoup) -> Dict[str, Dict[str, Any]]:
        """提取SEC标准的ITEM章节"""

        sections = {}

        self.logger.info("📋 开始识别SEC标准ITEM章节...")

        # 查找所有可能的ITEM标题
        item_headings = self._find_item_headings(soup)

        self.logger.info(f"🔍 找到 {len(item_headings)} 个ITEM标题")

        # 按照标准ITEM顺序处理
        for item_num, item_title in self.STANDARD_ITEMS.items():
            section_data = self._extract_single_item_content(
                soup, item_num, item_title, item_headings
            )

            if section_data:
                section_key = f"item_{item_num.lower()}"
                sections[section_key] = section_data

                content_length = len(section_data.get("content", ""))
                if content_length > 100:
                    self.logger.info(
                        f"✅ 提取 ITEM {item_num}: {item_title} ({content_length:,} 字符)"
                    )
                else:
                    self.logger.debug(
                        f"⚠️  ITEM {item_num}: {item_title} 内容较少 ({content_length} 字符)"
                    )

        return sections

    def _find_item_headings(self, soup: BeautifulSoup) -> List[Tuple[str, Tag, str]]:
        """查找所有ITEM标题元素 - 支持现代iXBRL文档"""

        item_headings = []
        processed_items = set()  # 避免重复

        # 专门针对iXBRL文档的ITEM模式
        item_number_pattern = r"ITEM\s*(\d+[A-C]?)\s*\.?\s*$"

        # 查找所有ITEM编号元素
        for element in soup.find_all(["span", "div", "p"]):
            text = element.get_text().strip()

            # 匹配纯ITEM编号（如"ITEM 1."）
            match = re.match(item_number_pattern, text, re.IGNORECASE)
            if match:
                item_number = match.group(1).upper()

                # 验证是否是有效的ITEM编号且未处理过
                if (
                    item_number in self.STANDARD_ITEMS
                    and item_number not in processed_items
                ):
                    # 查找对应的ITEM标题
                    item_title = self._find_item_title_for_number(element, item_number)

                    # 只保留在合理容器中的ITEM（避免表格中的重复）
                    if self._is_valid_item_context(element):
                        item_headings.append((item_number, element, item_title))
                        processed_items.add(item_number)

                        self.logger.debug(f"找到ITEM {item_number}: {item_title}")

        # 按ITEM编号排序
        item_headings.sort(key=lambda x: self._item_sort_key(x[0]))

        return item_headings

    def _find_item_title_for_number(self, item_element: Tag, item_number: str) -> str:
        """为ITEM编号查找对应的标题"""

        # 从标准映射获取默认标题
        default_title = self.STANDARD_ITEMS.get(item_number, "Unknown")

        # 策略1: 检查下一个兄弟节点
        next_sibling = item_element.next_sibling
        if next_sibling and hasattr(next_sibling, "get_text"):
            title_text = next_sibling.get_text().strip()
            if (
                title_text
                and len(title_text) < 100
                and not re.match(r"ITEM\s*\d+", title_text, re.IGNORECASE)
            ):
                return title_text

        # 策略2: 检查父元素的后续子元素
        if item_element.parent:
            siblings = list(item_element.parent.children)
            try:
                item_index = siblings.index(item_element)
                for i in range(item_index + 1, min(item_index + 3, len(siblings))):
                    sibling = siblings[i]
                    if hasattr(sibling, "get_text"):
                        title_text = sibling.get_text().strip()
                        if (
                            title_text
                            and len(title_text) < 100
                            and not re.match(r"ITEM\s*\d+", title_text, re.IGNORECASE)
                            and len(title_text) > 3
                        ):
                            return title_text
            except ValueError:
                pass

        # 策略3: 基于ITEM编号推断标题
        title_keywords = {
            "1": "Business",
            "1A": "Risk Factors",
            "1B": "Unresolved Staff Comments",
            "1C": "Cybersecurity",
            "2": "Properties",
            "3": "Legal Proceedings",
            "7": "Management Discussion and Analysis",
            "8": "Financial Statements",
        }

        return title_keywords.get(item_number, default_title)

    def _is_valid_item_context(self, element: Tag) -> bool:
        """检查ITEM元素是否在有效的上下文中"""

        # 避免表格中的ITEM（通常是目录）
        if element.find_parent("table"):
            return False

        # 检查是否在合理的文档结构中
        parent = element.parent
        while parent:
            # 如果在主要内容区域
            if parent.name in ["div", "body"] and parent.get("id"):
                return True
            # 如果在XBRL文档结构中
            if parent.name == "div" and (
                "xbrl" in str(parent.get("class", "")).lower()
                or "document" in str(parent.get("class", "")).lower()
            ):
                return True
            parent = parent.parent

        # 默认接受（但优先级较低）
        return True

    def _item_sort_key(self, item_num: str) -> Tuple[int, str]:
        """为ITEM编号生成排序键"""

        if item_num.isdigit():
            return (int(item_num), "")
        else:
            # 处理1A, 1B, 1C等格式
            base = re.match(r"(\d+)", item_num)
            suffix = re.search(r"([A-Z]+)", item_num)

            base_num = int(base.group(1)) if base else 999
            suffix_str = suffix.group(1) if suffix else ""

            return (base_num, suffix_str)

    def _extract_single_item_content(
        self,
        soup: BeautifulSoup,
        item_num: str,
        item_title: str,
        item_headings: List[Tuple[str, Tag, str]],
    ) -> Optional[Dict[str, Any]]:
        """提取单个ITEM的内容 - 采用内容块重构策略"""

        # 查找当前ITEM的标题元素
        current_heading_tuple = None
        next_heading_tuple = None

        for i, heading_tuple in enumerate(item_headings):
            if heading_tuple[0] == item_num:
                current_heading_tuple = heading_tuple
                # 找到下一个ITEM作为边界
                if i + 1 < len(item_headings):
                    next_heading_tuple = item_headings[i + 1]
                break

        if not current_heading_tuple:
            # 如果没有找到具体的标题，回退到文本搜索
            return self._extract_item_by_text_search(soup, item_num, item_title)

        current_heading_element = current_heading_tuple[1]
        next_heading_element = next_heading_tuple[1] if next_heading_tuple else None

        # 提取从当前ITEM到下一个ITEM之间的所有HTML内容块
        content_elements = self._extract_content_block(
            current_heading_element, next_heading_element
        )

        # 清理和合并文本内容
        cleaned_content = self._clean_and_merge_content(content_elements)

        # 如果主要方法没有提取到内容，尝试降级策略
        if not cleaned_content:
            fallback_content = self._extract_by_proximity_search(
                current_heading_element
            )
            if fallback_content:
                cleaned_content = self._clean_and_merge_content(fallback_content)

        return {
            "item_number": item_num,
            "title": item_title,
            "content": cleaned_content,
            "word_count": len(cleaned_content.split()),
            "char_count": len(cleaned_content),
            "extraction_method": "content_block" if cleaned_content else "fallback",
        }

    def _extract_content_block(
        self, start_element: Tag, end_element: Optional[Tag]
    ) -> List[str]:
        """
        提取两个元素之间的所有文本内容作为“内容块”。
        这是新的核心提取逻辑。
        """
        extracted_texts = []

        # 遍历从start_element开始的所有后续节点
        for sibling in start_element.find_all_next():
            # 如果到达了结束元素，停止遍历
            if end_element and sibling == end_element:
                break

            # 如果遇到了另一个ITEM标题，也停止（以防万一）
            if sibling.name in ["div", "span", "p"]:
                text = sibling.get_text().strip()
                if re.match(r"ITEM\s*\d+[A-C]?\s*\.?\s*$", text, re.IGNORECASE):
                    # 检查是否是真正的ITEM标题，而不是内容中的引用
                    if self._is_valid_item_context(sibling):
                        break

            # 筛选出包含实质性文本的标签
            if sibling.name in ["p", "div", "span", "td", "th"]:
                text = sibling.get_text(strip=True)
                # 过滤条件：长度超过30个字符且包含字母
                if len(text) > 30 and re.search(r"[a-zA-Z]", text):
                    # 进一步过滤掉纯粹的导航或目录链接
                    if not self._is_navigation_or_toc(text):
                        extracted_texts.append(" ".join(text.split()))  # 标准化空格

        return extracted_texts

    def _is_navigation_or_toc(self, text: str) -> bool:
        """判断文本是否可能是导航或目录链接。"""
        # 简单的启发式规则：如果文本很短，并且包含页码或"item"字样，则可能是目录
        text_lower = text.lower()
        if len(text.split()) < 15 and (
            "item" in text_lower or re.search(r"\d+$", text.strip())
        ):
            # 确保它不包含长句子结构
            if "." not in text or len(text) < 50:
                return True
        return False

    def _extract_by_proximity_search(self, item_element: Tag) -> List[str]:
        """通过临近搜索提取内容（最后降级策略）"""

        content_elements = []
        item_number = None

        # 从ITEM元素文本中提取编号
        item_text = item_element.get_text().strip()
        match = re.match(r"ITEM\s*(\d+[A-C]?)", item_text, re.IGNORECASE)
        if match:
            item_number = match.group(1).upper()

        if not item_number:
            return content_elements

        # 基于ITEM编号搜索相关关键词
        search_keywords = {
            "1": ["business", "operations", "segments", "products", "services"],
            "1A": ["risk factors", "risks", "uncertainties", "material adverse"],
            "7": [
                "management discussion",
                "financial condition",
                "results of operations",
            ],
            "8": ["financial statements", "consolidated statements"],
        }

        keywords = search_keywords.get(item_number, [])
        if not keywords:
            return content_elements

        # 在文档中搜索包含关键词的段落
        root_container = item_element.find_parent(["body", "html"]) or item_element

        for element in root_container.find_all(["div", "span", "p"]):
            text = element.get_text().strip().lower()
            if len(text) > 100:  # 只考虑较长的文本
                # 检查是否包含相关关键词
                keyword_matches = sum(1 for keyword in keywords if keyword in text)
                if keyword_matches >= 2:
                    content_elements.append(element.get_text().strip())
                    if len(content_elements) >= 3:  # 限制数量
                        break

        return content_elements

    def _extract_item_by_text_search(
        self, soup: BeautifulSoup, item_num: str, item_title: str
    ) -> Optional[Dict[str, Any]]:
        """通过文本搜索提取ITEM内容（降级策略） - 改进版本"""

        # 更精确的关键词映射，避免重复分类
        keyword_mapping = {
            "1": [
                "our business",
                "business segments",
                "principal products",
                "competition",
            ],
            "1A": [
                "risk factors",
                "risks include",
                "material adverse effect",
                "uncertainties",
            ],
            "1B": ["unresolved staff comments", "staff comments"],
            "1C": ["cybersecurity program", "cyber threats", "information security"],
            "2": ["properties include", "facilities", "square feet", "real estate"],
            "3": ["legal proceedings", "litigation", "lawsuits", "legal matters"],
            "7": [
                "management.s discussion",
                "results of operations",
                "liquidity and capital",
            ],
            "8": ["financial statements", "consolidated statements", "balance sheet"],
        }

        keywords = keyword_mapping.get(item_num, [])
        if not keywords:
            return None

        # 搜索包含关键词的段落，但要更严格的匹配
        relevant_paragraphs = []
        used_texts = set()  # 防止重复内容

        for para in soup.find_all(["p", "div"]):
            text = para.get_text().strip()
            text_lower = text.lower()

            # 检查文本长度和质量
            if len(text) < 50 or text in used_texts:
                continue

            # 计算关键词匹配度
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches >= 2 or (matches >= 1 and len(keywords) <= 2):
                relevant_paragraphs.append(text)
                used_texts.add(text)

                # 限制每个章节的段落数量
                if len(relevant_paragraphs) >= 5:
                    break

        if relevant_paragraphs:
            cleaned_content = self._clean_and_merge_content(relevant_paragraphs)

            return {
                "item_number": item_num,
                "title": item_title,
                "content": cleaned_content,
                "word_count": len(cleaned_content.split()),
                "char_count": len(cleaned_content),
                "extraction_method": "keyword_search",
            }

        return None

    def _clean_and_merge_content(self, content_elements: List[str]) -> str:
        """清理和合并文本内容，增加行级去重以处理财务报表中的重复文本。"""

        if not content_elements:
            return ""

        # 1. 将所有提取到的内容块合并成一个大的文本字符串。
        full_text = "\n".join(content_elements)

        # 2. 按行分割文本，并进行去重。
        lines = full_text.split("\n")
        unique_lines = []
        seen_lines_signatures = set()

        for line in lines:
            stripped_line = line.strip()

            # 如果行太短或没有字母，则可能是格式化的空行或分隔符，跳过
            if len(stripped_line) < 2 or not re.search(r"[a-zA-Z]", stripped_line):
                continue

            # 为了更有效地去重，我们将行转换为小写并提取单词来创建“签名”
            line_signature = tuple(re.findall(r"\b\w+\b", stripped_line.lower()))

            if not line_signature:
                continue

            if line_signature not in seen_lines_signatures:
                unique_lines.append(stripped_line)  # 保存原始的、清理过的行
                seen_lines_signatures.add(line_signature)

        # 3. 将唯一的行重新组合成最终内容。
        merged_content = "\n\n".join(unique_lines)

        # 4. 执行最终的全局清理
        merged_content = re.sub(r"&nbsp;", " ", merged_content)
        merged_content = re.sub(r"&lt;", "<", merged_content)
        merged_content = re.sub(r"&gt;", ">", merged_content)
        merged_content = re.sub(r"&amp;", "&", merged_content)
        merged_content = re.sub(r"&#\d+;", "", merged_content)

        # 移除多余的空白
        merged_content = re.sub(r"\n\s*\n\s*\n+", "\n\n", merged_content)
        merged_content = re.sub(r"[ \t]+", " ", merged_content)

        return merged_content.strip()

    def _extract_text_from_tables(self, soup: BeautifulSoup) -> List[str]:
        """从表格中提取重要的叙述性文本（如附注）"""

        narrative_texts = []

        for table in soup.find_all("table"):
            # 在每个表格中查找包含长文本的单元格
            for cell in table.find_all(["td", "th"]):
                text = cell.get_text().strip()

                # 筛选条件：
                # 1. 文本长度超过100个字符
                # 2. 包含字母，以排除纯数字行
                # 3. 不是表格标题（通常在caption或少数几个单元格）
                if len(text) > 100 and re.search(r"[a-zA-Z]", text):
                    # 避免提取已经作为标题的内容
                    if "item" not in text.lower() and "part" not in text.lower():
                        narrative_texts.append(text)

        return narrative_texts

    def _extract_structured_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取并结构化表格数据"""

        tables = []
        html_tables = soup.find_all("table")

        self.logger.info(f"📊 处理 {len(html_tables)} 个表格...")

        for i, table in enumerate(html_tables):
            try:
                table_data = self._process_single_table(table, i)
                if table_data:
                    tables.append(table_data)
            except Exception as e:
                self.logger.warning(f"处理表格 {i} 时出错: {e}")
                continue

        self.logger.info(f"✅ 成功处理 {len(tables)} 个表格")
        return tables

    def _process_single_table(
        self, table: Tag, table_index: int
    ) -> Optional[Dict[str, Any]]:
        """处理单个表格"""

        # 尝试用pandas处理
        try:
            df = pd.read_html(StringIO(str(table)))[0]

            # 清理数据
            df = df.fillna("")

            # 转换为字典格式
            table_dict = {
                "headers": df.columns.tolist(),
                "data": df.values.tolist(),
                "row_count": len(df),
                "col_count": len(df.columns),
            }

            return {
                "table_id": f"table_{table_index}",
                "title": f"Table {table_index + 1}",
                "type": "general",
                "structure": table_dict,
                "extraction_method": "pandas",
            }

        except Exception as e:
            return None

    def _extract_xbrl_facts(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取XBRL结构化数据"""

        xbrl_facts = {}

        try:
            # 提取inline XBRL数据
            ix_elements = soup.find_all(["ix:nonnumeric", "ix:nonfraction"])

            for elem in ix_elements:
                name = elem.get("name")
                if name:
                    value = elem.get_text().strip()
                    context = elem.get("contextref")
                    unit = elem.get("unitref")

                    if name not in xbrl_facts:
                        xbrl_facts[name] = []

                    xbrl_facts[name].append(
                        {
                            "value": value,
                            "context": context,
                            "unit": unit,
                            "decimals": elem.get("decimals"),
                            "scale": elem.get("scale"),
                        }
                    )

            self.logger.info(f"📊 提取了 {len(xbrl_facts)} 个XBRL数据点")

        except Exception as e:
            self.logger.warning(f"提取XBRL数据时出错: {e}")

        return xbrl_facts

    def _calculate_processing_stats(
        self, sections: Dict, tables: List, xbrl_data: Dict
    ) -> Dict[str, Any]:
        """计算处理统计信息"""

        total_text_length = sum(
            len(section.get("content", "")) for section in sections.values()
        )
        sections_with_content = sum(
            1 for section in sections.values() if len(section.get("content", "")) > 100
        )

        return {
            "sections_extracted": len(sections),
            "sections_with_substantial_content": sections_with_content,
            "total_text_length": total_text_length,
            "tables_extracted": len(tables),
            "xbrl_facts_extracted": len(xbrl_data),
            "average_section_length": total_text_length // max(len(sections), 1),
        }


class EDGARReportDownloader:
    """EDGAR文件下载器 - 支持10-K和13F-HR表单"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": f'{self.config["user_agent"]["email"]} Python SEC API Client'
            }
        )
        self.logger = logging.getLogger(__name__)

        # 根据表单类型初始化对应的提取器
        self.form_type = self.config.get("form_type", "10-K")
        self.extractor_10k = SECStandardExtractor()
        self.extractor_13f = SEC13FExtractor()

        # 创建输出目录
        os.makedirs(
            self.config["download_settings"]["download_directory"], exist_ok=True
        )
        os.makedirs(
            self.config["conversion_settings"]["json_output_directory"], exist_ok=True
        )

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"配置文件 {self.config_path} 不存在")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {e}")
            raise

    def run(self):
        """运行完整的下载和处理流程"""

        form_type = self.config.get("form_type", "10-K")
        self.logger.info(f"🚀 开始EDGAR {form_type} 文件下载和处理...")

        # 解析股票代码
        tickers = [
            ticker.strip() for ticker in self.config["companies"]["tickers"].split(",")
        ]
        self.logger.info(f"📊 处理股票: {tickers}")
        self.logger.info(f"📋 表单类型: {form_type}")

        # 解析年份范围
        start_year, end_year = self._parse_year_range(
            self.config["download_settings"]["year_range"]
        )
        self.logger.info(f"📅 年份范围: {start_year}-{end_year}")

        total_processed = 0
        total_errors = 0

        # 为每个股票下载报告
        for ticker in tickers:
            try:
                self.logger.info(f"\n{'='*50}")
                self.logger.info(f"📈 处理股票: {ticker}")
                self.logger.info(f"{'='*50}")

                processed, errors = self._process_ticker(
                    ticker, start_year, end_year, form_type
                )
                total_processed += processed
                total_errors += errors

            except Exception as e:
                self.logger.error(f"处理股票 {ticker} 时出错: {e}")
                total_errors += 1
                continue

        # 输出最终统计
        self.logger.info(f"\n🎯 处理完成统计:")
        self.logger.info(f"✅ 成功处理: {total_processed} 个报告")
        self.logger.info(f"❌ 处理失败: {total_errors} 个")
        self.logger.info(
            f"📊 成功率: {total_processed/(total_processed+total_errors)*100:.1f}%"
            if (total_processed + total_errors) > 0
            else "N/A"
        )

    def _parse_year_range(self, year_range: str) -> Tuple[int, int]:
        """解析年份范围"""

        if "-" in year_range:
            # 年份范围格式: "2020-2025"
            start_str, end_str = year_range.split("-")
            return int(start_str.strip()), int(end_str.strip())
        else:
            # 单年格式: "2025"
            year = int(year_range.strip())
            return year, year

    def _process_ticker(
        self, ticker: str, start_year: int, end_year: int, form_type: str = "10-K"
    ) -> Tuple[int, int]:
        """处理单个股票的所有年份"""

        processed_count = 0
        error_count = 0

        # 获取CIK
        cik = self._get_cik_for_ticker(ticker)
        if not cik:
            self.logger.error(f"无法获取 {ticker} 的CIK")
            return 0, 1

        self.logger.info(f"📋 {ticker} CIK: {cik}")

        # 获取指定类型的文件列表
        filings = self._get_filings(cik, form_type, start_year, end_year)
        if not filings:
            self.logger.warning(
                f"没有找到 {ticker} 在 {start_year}-{end_year} 的{form_type}文件"
            )
            return 0, 1

        self.logger.info(f"📄 找到 {len(filings)} 个{form_type}文件")

        # 检查缺失的年份
        available_years = set()
        for filing in filings:
            filing_year = pd.to_datetime(filing["filingDate"]).year
            available_years.add(filing_year)

        requested_years = set(range(start_year, end_year + 1))
        missing_years = requested_years - available_years

        if missing_years:
            self.logger.warning(f"⚠️  缺失年份: {sorted(missing_years)}")

        # 下载和处理每个文件
        for filing in filings:
            try:
                filing_date = filing["filingDate"]
                filing_year = pd.to_datetime(filing_date).year

                if start_year <= filing_year <= end_year:
                    # 添加表单类型到filing字典
                    filing["formType"] = form_type
                    success = self._download_and_process_filing(ticker, cik, filing)
                    if success:
                        processed_count += 1
                    else:
                        error_count += 1

            except Exception as e:
                self.logger.error(f"处理文件时出错: {e}")
                error_count += 1
                continue

        return processed_count, error_count

    def _get_cik_for_ticker(self, ticker: str) -> Optional[str]:
        """获取股票代码对应的CIK"""

        cache_file = self.config.get("cache_settings", {}).get(
            "cache_file", "ticker_cik_cache.json"
        )

        # 尝试从缓存读取
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cache = json.load(f)
                    if ticker in cache:
                        return cache[ticker]
            except:
                pass

        # 从SEC API获取
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()

            # 创建缓存
            cache = {}
            for entry in data.values():
                cache[entry["ticker"]] = str(entry["cik_str"]).zfill(10)

            # 保存缓存
            with open(cache_file, "w") as f:
                json.dump(cache, f, indent=2)

            return cache.get(ticker)

        except Exception as e:
            self.logger.error(f"获取CIK时出错: {e}")
            return None

    def _get_filings(
        self, cik: str, form_type: str, start_year: int, end_year: int
    ) -> List[Dict[str, Any]]:
        """获取指定年份范围和表单类型的文件列表"""

        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()
            filings = data.get("filings", {}).get("recent", {})

            # 过滤指定类型的文件
            filing_list = []
            for i, form in enumerate(filings.get("form", [])):
                if form == form_type:
                    filing_date = filings["filingDate"][i]
                    filing_year = pd.to_datetime(filing_date).year

                    if start_year <= filing_year <= end_year:
                        filing_list.append(
                            {
                                "filingDate": filing_date,
                                "accessionNumber": filings["accessionNumber"][i],
                                "primaryDocument": filings["primaryDocument"][i],
                            }
                        )

            # 按日期排序
            filing_list.sort(key=lambda x: x["filingDate"])

            return filing_list

        except Exception as e:
            self.logger.error(f"获取{form_type}文件列表时出错: {e}")
            return []

    def _download_and_process_filing(
        self, ticker: str, cik: str, filing: Dict[str, Any]
    ) -> bool:
        """下载并处理单个文件 - 根据表单类型选择处理方式"""

        form_type = filing.get("formType", "10-K")

        if form_type == "10-K":
            return self._download_and_process_10k(ticker, cik, filing)
        elif form_type == "13F-HR":
            return self._download_and_process_13f(ticker, cik, filing)
        else:
            self.logger.error(f"不支持的表单类型: {form_type}")
            return False

    def _download_and_process_10k(
        self, ticker: str, cik: str, filing: Dict[str, Any]
    ) -> bool:
        """下载并处理10-K文件"""

        try:
            # 构建文件URL
            accession = filing["accessionNumber"].replace("-", "")
            primary_doc = filing["primaryDocument"]
            filing_date = filing["filingDate"]

            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}"

            # 构建本地文件名
            html_filename = f"{ticker}_CIK_{cik}_FORM_10-K_{filing_date}.html"
            json_filename = f"{ticker}_CIK_{cik}_FORM_10-K_{filing_date}.json"

            html_path = os.path.join(
                self.config["download_settings"]["download_directory"], html_filename
            )
            json_path = os.path.join(
                self.config["conversion_settings"]["json_output_directory"],
                json_filename,
            )

            self.logger.info(f"📥 下载: {filing_date} 10-K")

            # 下载HTML文件
            if not os.path.exists(html_path):
                response = self.session.get(url)
                response.raise_for_status()

                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(response.text)

                # 限制请求频率
                time.sleep(0.1)
            else:
                self.logger.info(f"📄 文件已存在，跳过下载: {html_filename}")

            # 转换为JSON
            if self.config["conversion_settings"]["enable_json_conversion"]:
                self.logger.info(f"🔄 转换为结构化JSON...")

                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                # 使用SEC标准提取器
                structured_data = self.extractor_10k.extract_sec_sections(
                    html_content, html_path
                )

                # 保存JSON
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(structured_data, f, indent=2, ensure_ascii=False)

                # 输出统计信息
                stats = structured_data["processing_stats"]
                self.logger.info(
                    f"✅ 完成: {stats['sections_with_substantial_content']}/{stats['sections_extracted']} 章节, "
                    f"{stats['tables_extracted']} 表格, {stats['total_text_length']:,} 字符"
                )

            return True

        except Exception as e:
            self.logger.error(f"下载和处理10-K文件时出错: {e}")
            return False

    def _download_and_process_13f(
        self, ticker: str, cik: str, filing: Dict[str, Any]
    ) -> bool:
        """下载并处理13F-HR文件"""

        try:
            accession = filing["accessionNumber"]
            accession_clean = accession.replace("-", "")
            filing_date = filing["filingDate"]

            # 13F的信息表通常嵌入在完整的申报文件中
            # 下载完整的申报文件
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}.txt"

            self.logger.info(f"📥 下载13F完整申报文件...")
            response = self.session.get(filing_url)

            if response.status_code != 200:
                self.logger.error(f"❌ 无法下载申报文件: HTTP {response.status_code}")
                return False

            # 解析SGML格式，提取信息表
            content = response.text
            xml_content = self._extract_information_table_from_filing(content)

            if not xml_content:
                self.logger.error(f"❌ 无法从申报文件中提取信息表")
                return False

            self.logger.info(f"✅ 成功提取信息表 ({len(xml_content)} 字节)")

            # 保存原始XML文件
            xml_filename = f"{ticker}_CIK_{cik}_FORM_13F-HR_{filing_date}.xml"
            json_filename = f"{ticker}_CIK_{cik}_FORM_13F-HR_{filing_date}.json"

            xml_path = os.path.join(
                self.config["download_settings"]["download_directory"], xml_filename
            )
            json_path = os.path.join(
                self.config["conversion_settings"]["json_output_directory"],
                json_filename,
            )

            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_content)

            self.logger.info(f"💾 保存XML文件: {xml_filename}")

            # 转换为JSON
            if self.config["conversion_settings"]["enable_json_conversion"]:
                self.logger.info(f"🔄 解析13F持仓数据...")

                # 使用13F提取器
                structured_data = self.extractor_13f.extract_13f_data(
                    xml_content, xml_path
                )

                # 保存JSON
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(structured_data, f, indent=2, ensure_ascii=False)

                # 输出统计信息
                stats = structured_data["summary_statistics"]
                self.logger.info(
                    f"✅ 完成: {stats['total_positions']} 个持仓, "
                    f"总市值: ${stats['total_value_usd']:,.0f}"
                )

            # 限制请求频率
            time.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"下载和处理13F文件时出错: {e}")
            return False

    def _extract_information_table_from_filing(
        self, filing_content: str
    ) -> Optional[str]:
        """从完整的SGML申报文件中提取信息表XML"""

        try:
            documents = []
            current_doc = None
            in_content = False

            for line in filing_content.split("\n"):
                if line.startswith("<DOCUMENT>"):
                    current_doc = {"content": []}
                    in_content = False
                elif line.startswith("</DOCUMENT>"):
                    if current_doc:
                        documents.append(current_doc)
                    current_doc = None
                    in_content = False
                elif line.startswith("<TYPE>"):
                    if current_doc is not None:
                        current_doc["type"] = line.split(">")[1].strip()
                elif line.startswith("<FILENAME>"):
                    if current_doc is not None:
                        current_doc["filename"] = line.split(">")[1].strip()
                elif line.startswith("<TEXT>"):
                    in_content = True
                elif line.startswith("</TEXT>"):
                    in_content = False
                elif current_doc is not None and in_content:
                    current_doc["content"].append(line)

            # 查找信息表文档
            for doc in documents:
                if doc.get("type") == "INFORMATION TABLE":
                    xml_content = "\n".join(doc["content"])
                    return xml_content

            return None

        except Exception as e:
            self.logger.error(f"提取信息表时出错: {e}")
            return None


def main():
    """主程序入口"""

    print("🚀 EDGAR年报下载器和清洗器 v2.2")
    print("=" * 50)

    try:
        downloader = EDGARReportDownloader()
        downloader.run()

    except KeyboardInterrupt:
        print("\n⚠️  用户中断程序")
    except Exception as e:
        print(f"❌ 程序出错: {e}")
        raise


if __name__ == "__main__":
    main()
