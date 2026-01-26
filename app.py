#!/usr/bin/env python3
"""
13F Web Application - Flask Backend
用于下载和分析13F持仓报告的Web应用后端
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# 添加EDGAR模块路径
EDGAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "EDGAR")
sys.path.insert(0, EDGAR_PATH)

from edgar_downloader import EDGARReportDownloader
from sec_13f_extractor import SEC13FExtractor

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# 配置路径
JSON_REPORTS_DIR = os.path.join(EDGAR_PATH, "JSON_Reports")
SEC_FILINGS_DIR = os.path.join(EDGAR_PATH, "SEC_Filings")
CONFIG_PATH = os.path.join(EDGAR_PATH, "config.json")

# CIK到公司名称的缓存
CIK_COMPANY_NAME_CACHE = {}


def get_company_name_by_cik(cik):
    """通过CIK获取公司名称"""
    import requests

    cik_formatted = cik.zfill(10)

    # 检查缓存
    if cik_formatted in CIK_COMPANY_NAME_CACHE:
        return CIK_COMPANY_NAME_CACHE[cik_formatted]

    try:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "PersonalResearch your_email@example.com Python SEC API Client"
            }
        )

        url = f"https://data.sec.gov/submissions/CIK{cik_formatted}.json"
        response = session.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            company_name = data.get("name", f"CIK {cik}")
            CIK_COMPANY_NAME_CACHE[cik_formatted] = company_name
            return company_name
    except Exception as e:
        logger.warning(f"获取公司名称失败 CIK {cik}: {e}")

    return f"CIK {cik}"


def get_quarter_from_date(date_str):
    """从日期字符串获取季度信息"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        quarter = (date.month - 1) // 3 + 1
        return f"Q{quarter} {date.year}"
    except:
        return "Unknown"


def get_available_reports():
    """获取所有已下载的13F报告"""
    reports = []
    if not os.path.exists(JSON_REPORTS_DIR):
        return reports

    for filename in os.listdir(JSON_REPORTS_DIR):
        if "13F-HR" in filename and filename.endswith(".json"):
            try:
                filepath = os.path.join(JSON_REPORTS_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data.get("document_metadata", {})

                # 从文件名解析信息 (格式: TICKER_CIK_XXXXXXXXXX_FORM_13F-HR_YYYY-MM-DD.json)
                import re

                filename_match = re.search(
                    r"CIK_(\d+)_FORM_13F-HR_(\d{4}-\d{2}-\d{2})", filename
                )

                # 优先从文件名获取CIK和日期（更可靠）
                if filename_match:
                    cik = filename_match.group(1).lstrip("0")
                    filing_date = filename_match.group(2)
                else:
                    # 回退到元数据
                    cik = metadata.get("cik", "").lstrip("0")
                    filing_date = metadata.get("filing_date", "")

                # 从文件名解析ticker
                parts = filename.split("_")
                ticker = parts[0] if parts else "Unknown"

                # 获取公司名称 - 优先使用元数据中的名称，否则从SEC API获取
                company_name = metadata.get("filing_manager", "Unknown")
                if company_name == "Unknown" or company_name.startswith("CIK "):
                    # 从SEC API获取真正的公司名称
                    if cik:
                        company_name = get_company_name_by_cik(cik)

                reports.append(
                    {
                        "filename": filename,
                        "filing_date": filing_date,
                        "quarter": get_quarter_from_date(filing_date),
                        "cik": cik,
                        "ticker": ticker,
                        "company_name": company_name,
                        "total_value": data.get("summary_statistics", {}).get(
                            "total_value_usd", 0
                        ),
                        "total_positions": data.get("summary_statistics", {}).get(
                            "total_positions", 0
                        ),
                    }
                )
            except Exception as e:
                logger.error(f"Error reading {filename}: {e}")
                continue

    # 按日期排序
    reports.sort(key=lambda x: x["filing_date"], reverse=True)
    return reports


@app.route("/")
def index():
    """返回console页面"""
    return send_from_directory(".", "console.html")


@app.route("/dashboard")
def dashboard():
    """返回dashboard页面"""
    return send_from_directory(".", "dashboard.html")


@app.route("/api/download", methods=["POST"])
def download_13f():
    """下载指定CIK和时间段的13F报告"""
    try:
        data = request.json
        cik = data.get("cik", "").strip()
        year = data.get("year", "")
        quarter = data.get("quarter", "")

        if not cik:
            return jsonify({"error": "CIK is required"}), 400

        if not year:
            return jsonify({"error": "Year is required"}), 400

        logger.info(f"下载请求: CIK={cik}, Year={year}, Quarter={quarter}")

        # 创建临时配置
        temp_config = {
            "form_type": "13F-HR",
            "companies": {"tickers": f"CIK{cik.zfill(10)}", "cik": cik.zfill(10)},
            "download_settings": {
                "year_range": str(year),
                "download_directory": SEC_FILINGS_DIR,
            },
            "conversion_settings": {
                "enable_json_conversion": True,
                "json_output_directory": JSON_REPORTS_DIR,
            },
            "user_agent": {"email": "your_email@example.com"},
        }

        # 保存临时配置
        temp_config_path = os.path.join(EDGAR_PATH, "config_temp.json")
        with open(temp_config_path, "w") as f:
            json.dump(temp_config, f, indent=2)

        # 直接使用EDGAR下载器的内部方法
        import requests

        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "PersonalResearch your_email@example.com Python SEC API Client"
            }
        )

        # 格式化CIK
        cik_formatted = cik.zfill(10)

        # 获取filing列表
        url = f"https://data.sec.gov/submissions/CIK{cik_formatted}.json"
        response = session.get(url)

        if response.status_code != 200:
            return (
                jsonify({"error": f"无法获取CIK {cik} 的信息，请确认CIK号码正确"}),
                400,
            )

        company_data = response.json()
        company_name = company_data.get("name", f"CIK {cik}")

        filings = company_data.get("filings", {}).get("recent", {})

        # 过滤13F-HR
        filing_list = []
        for i, form in enumerate(filings.get("form", [])):
            if form == "13F-HR":
                filing_date = filings["filingDate"][i]
                filing_year = int(filing_date[:4])
                filing_month = int(filing_date[5:7])
                filing_quarter = (filing_month - 1) // 3 + 1

                # 检查年份和季度匹配
                if str(filing_year) == str(year):
                    if not quarter or str(filing_quarter) == str(quarter):
                        filing_list.append(
                            {
                                "filingDate": filing_date,
                                "accessionNumber": filings["accessionNumber"][i],
                                "primaryDocument": filings["primaryDocument"][i],
                            }
                        )

        if not filing_list:
            return (
                jsonify(
                    {
                        "error": f'未找到 {company_name} (CIK: {cik}) 在 {year}年{f"Q{quarter}" if quarter else ""} 的13F报告'
                    }
                ),
                404,
            )

        # 下载找到的报告
        downloaded = []
        extractor = SEC13FExtractor()

        for filing in filing_list:
            try:
                accession = filing["accessionNumber"]
                accession_clean = accession.replace("-", "")
                filing_date = filing["filingDate"]

                # 下载完整申报文件
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_formatted}/{accession_clean}/{accession}.txt"
                resp = session.get(filing_url)

                if resp.status_code != 200:
                    continue

                # 提取信息表
                content = resp.text
                xml_content = extract_information_table(content)

                if not xml_content:
                    continue

                # 保存文件
                ticker = company_name.split()[0] if company_name else f"CIK{cik}"
                ticker = "".join(c for c in ticker if c.isalnum())[:10]

                xml_filename = (
                    f"{ticker}_CIK_{cik_formatted}_FORM_13F-HR_{filing_date}.xml"
                )
                json_filename = (
                    f"{ticker}_CIK_{cik_formatted}_FORM_13F-HR_{filing_date}.json"
                )

                xml_path = os.path.join(SEC_FILINGS_DIR, xml_filename)
                json_path = os.path.join(JSON_REPORTS_DIR, json_filename)

                # 确保目录存在
                os.makedirs(SEC_FILINGS_DIR, exist_ok=True)
                os.makedirs(JSON_REPORTS_DIR, exist_ok=True)

                with open(xml_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)

                # 解析并保存JSON
                structured_data = extractor.extract_13f_data(xml_content, xml_path)

                # 添加公司名称到元数据
                structured_data["document_metadata"]["filing_manager"] = company_name

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(structured_data, f, indent=2, ensure_ascii=False)

                downloaded.append(
                    {
                        "filename": json_filename,
                        "filing_date": filing_date,
                        "quarter": get_quarter_from_date(filing_date),
                        "company_name": company_name,
                        "total_value": structured_data.get(
                            "summary_statistics", {}
                        ).get("total_value_usd", 0),
                        "total_positions": structured_data.get(
                            "summary_statistics", {}
                        ).get("total_positions", 0),
                    }
                )

                import time

                time.sleep(0.2)  # SEC请求限制

            except Exception as e:
                logger.error(f"下载失败: {e}")
                continue

        if downloaded:
            return jsonify(
                {
                    "success": True,
                    "message": f"成功下载 {len(downloaded)} 个13F报告",
                    "company_name": company_name,
                    "downloaded": downloaded,
                }
            )
        else:
            return jsonify({"error": "下载失败，请稍后重试"}), 500

    except Exception as e:
        logger.error(f"下载错误: {e}")
        return jsonify({"error": str(e)}), 500


def extract_information_table(filing_content):
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
            elif line.startswith("<TEXT>"):
                in_content = True
            elif line.startswith("</TEXT>"):
                in_content = False
            elif current_doc is not None and in_content:
                current_doc["content"].append(line)

        for doc in documents:
            if doc.get("type") == "INFORMATION TABLE":
                return "\n".join(doc["content"])

        return None
    except Exception as e:
        logger.error(f"提取信息表时出错: {e}")
        return None


@app.route("/api/reports")
def get_reports():
    """获取所有已下载的报告列表"""
    reports = get_available_reports()

    # 按CIK分组
    grouped = {}
    for report in reports:
        cik = report["cik"]
        if cik not in grouped:
            grouped[cik] = {
                "cik": cik,
                "company_name": report["company_name"],
                "quarters": [],
            }
        grouped[cik]["quarters"].append(
            {
                "filename": report["filename"],
                "filing_date": report["filing_date"],
                "quarter": report["quarter"],
                "total_value": report["total_value"],
                "total_positions": report["total_positions"],
            }
        )

    return jsonify({"reports": list(grouped.values()), "total": len(reports)})


@app.route("/api/report/<filename>")
def get_report_detail(filename):
    """获取单个报告的详细信息"""
    try:
        filepath = os.path.join(JSON_REPORTS_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "Report not found"}), 404

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/delete", methods=["POST"])
def delete_reports():
    """删除选中的报告"""
    try:
        data = request.get_json()
        filenames = data.get("filenames", [])

        if not filenames:
            return jsonify({"error": "No filenames provided"}), 400

        deleted_count = 0
        errors = []

        for filename in filenames:
            try:
                # 删除JSON文件
                json_filepath = os.path.join(JSON_REPORTS_DIR, filename)
                if os.path.exists(json_filepath):
                    os.remove(json_filepath)
                    deleted_count += 1

                    # 同时删除对应的XML文件
                    xml_filename = filename.replace(".json", ".xml")
                    xml_filepath = os.path.join(SEC_FILINGS_DIR, xml_filename)
                    if os.path.exists(xml_filepath):
                        os.remove(xml_filepath)

                    logger.info(f"Deleted report: {filename}")
                else:
                    errors.append(f"File not found: {filename}")
            except Exception as e:
                errors.append(f"Error deleting {filename}: {str(e)}")

        response = {"deleted": deleted_count, "total": len(filenames)}
        if errors:
            response["errors"] = errors

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error deleting reports: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analysis/<filename>")
def get_analysis(filename):
    """获取报告分析数据，包括与上季度的对比"""
    try:
        filepath = os.path.join(JSON_REPORTS_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "Report not found"}), 404

        with open(filepath, "r", encoding="utf-8") as f:
            current_data = json.load(f)

        # 获取元数据（用于公司名称等）
        metadata = current_data.get("document_metadata", {})

        # 从文件名中提取CIK和日期 (更可靠)
        import re

        filename_match = re.search(
            r"CIK_(\d+)_FORM_13F-HR_(\d{4}-\d{2}-\d{2})", filename
        )

        if filename_match:
            cik = filename_match.group(1).lstrip("0")
            current_date = filename_match.group(2)
        else:
            # 回退到元数据
            current_date = metadata.get("filing_date", "")
            cik = metadata.get("cik", "").lstrip("0")

        logger.info(f"Analyzing report: CIK={cik}, Date={current_date}")

        # 查找上一季度的报告
        all_reports = get_available_reports()
        previous_data = None
        previous_report_info = None

        # 过滤同一CIK的报告，按日期排序
        same_cik_reports = [r for r in all_reports if r["cik"].lstrip("0") == cik]
        same_cik_reports.sort(key=lambda x: x["filing_date"], reverse=True)

        logger.info(f"Found {len(same_cik_reports)} reports for CIK {cik}")

        for report in same_cik_reports:
            if report["filing_date"] < current_date:
                prev_filepath = os.path.join(JSON_REPORTS_DIR, report["filename"])
                if os.path.exists(prev_filepath):
                    with open(prev_filepath, "r", encoding="utf-8") as f:
                        previous_data = json.load(f)
                    previous_report_info = report
                    logger.info(f"Found previous report: {report['filename']}")
                break

        # 分析当前持仓
        holdings = current_data.get("holdings", [])

        # 按公司聚合持仓
        current_holdings = {}
        for h in holdings:
            issuer = h.get("issuer_name", "Unknown")
            cusip = h.get("cusip", "")
            key = f"{issuer}_{cusip}"

            if key not in current_holdings:
                current_holdings[key] = {
                    "issuer_name": issuer,
                    "cusip": cusip,
                    "title_of_class": h.get("title_of_class", ""),
                    "value_usd": 0,
                    "shares": 0,
                }

            current_holdings[key]["value_usd"] += h.get("value_usd", 0)
            current_holdings[key]["shares"] += h.get("shares_or_principal", {}).get(
                "amount", 0
            )

        # 分析上期持仓
        previous_holdings = {}
        if previous_data:
            for h in previous_data.get("holdings", []):
                issuer = h.get("issuer_name", "Unknown")
                cusip = h.get("cusip", "")
                key = f"{issuer}_{cusip}"

                if key not in previous_holdings:
                    previous_holdings[key] = {
                        "issuer_name": issuer,
                        "cusip": cusip,
                        "value_usd": 0,
                        "shares": 0,
                    }

                previous_holdings[key]["value_usd"] += h.get("value_usd", 0)
                previous_holdings[key]["shares"] += h.get(
                    "shares_or_principal", {}
                ).get("amount", 0)

        # 计算变化
        increases = []
        decreases = []
        new_positions = []
        exited_positions = []

        # 统计期权
        call_options = []
        put_options = []

        for key, holding in current_holdings.items():
            title = holding.get("title_of_class", "").upper()

            # 识别期权
            if "CALL" in title:
                call_options.append(holding)
            elif "PUT" in title:
                put_options.append(holding)

            if key in previous_holdings:
                prev = previous_holdings[key]
                share_change = holding["shares"] - prev["shares"]
                value_change = holding["value_usd"] - prev["value_usd"]

                if share_change > 0:
                    increases.append(
                        {
                            "issuer_name": holding["issuer_name"],
                            "share_change": share_change,
                            "value_change": value_change,
                            "current_shares": holding["shares"],
                            "previous_shares": prev["shares"],
                            "current_value": holding["value_usd"],
                            "percent_change": (
                                (share_change / prev["shares"] * 100)
                                if prev["shares"] > 0
                                else 0
                            ),
                        }
                    )
                elif share_change < 0:
                    decreases.append(
                        {
                            "issuer_name": holding["issuer_name"],
                            "share_change": share_change,
                            "value_change": value_change,
                            "current_shares": holding["shares"],
                            "previous_shares": prev["shares"],
                            "current_value": holding["value_usd"],
                            "percent_change": (
                                (share_change / prev["shares"] * 100)
                                if prev["shares"] > 0
                                else 0
                            ),
                        }
                    )
            else:
                new_positions.append(
                    {
                        "issuer_name": holding["issuer_name"],
                        "shares": holding["shares"],
                        "value": holding["value_usd"],
                    }
                )

        # 找出退出的持仓
        for key, holding in previous_holdings.items():
            if key not in current_holdings:
                exited_positions.append(
                    {
                        "issuer_name": holding["issuer_name"],
                        "shares": holding["shares"],
                        "value": holding["value_usd"],
                    }
                )

        # 排序
        increases.sort(key=lambda x: abs(x["share_change"]), reverse=True)
        decreases.sort(key=lambda x: abs(x["share_change"]), reverse=True)

        # 计算统计数据
        total_value = sum(h["value_usd"] for h in current_holdings.values())
        call_value = sum(h["value_usd"] for h in call_options)
        put_value = sum(h["value_usd"] for h in put_options)
        options_value = call_value + put_value
        put_call_ratio = put_value / call_value if call_value > 0 else 0

        # 对比上季度
        previous_total = (
            sum(h["value_usd"] for h in previous_holdings.values())
            if previous_holdings
            else 0
        )
        value_change = total_value - previous_total if previous_total > 0 else 0
        value_change_percent = (
            (value_change / previous_total * 100) if previous_total > 0 else 0
        )

        return jsonify(
            {
                "summary": {
                    "total_value": total_value,
                    "previous_total_value": previous_total,
                    "value_change": value_change,
                    "value_change_percent": value_change_percent,
                    "total_positions": len(current_holdings),
                    "options_value": options_value,
                    "call_value": call_value,
                    "put_value": put_value,
                    "put_call_ratio": round(put_call_ratio, 2),
                    "new_positions_count": len(new_positions),
                    "exited_positions_count": len(exited_positions),
                    "increased_count": len(increases),
                    "decreased_count": len(decreases),
                },
                "increases": increases[:10],  # Top 10
                "decreases": decreases[:10],  # Top 10
                "new_positions": new_positions[:10],
                "exited_positions": exited_positions[:10],
                "call_options": sorted(
                    call_options, key=lambda x: x["value_usd"], reverse=True
                )[:5],
                "put_options": sorted(
                    put_options, key=lambda x: x["value_usd"], reverse=True
                )[:5],
                "has_previous_quarter": previous_data is not None,
                "quarter": get_quarter_from_date(current_date),
                "filing_date": current_date,
                "company_name": metadata.get("filing_manager", "Unknown"),
            }
        )

    except Exception as e:
        logger.error(f"分析错误: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/entities")
def get_entities():
    """获取所有已下载报告对应的机构列表"""
    reports = get_available_reports()

    entities = {}
    for report in reports:
        cik = report["cik"]
        if cik not in entities:
            entities[cik] = {"cik": cik, "name": report["company_name"], "quarters": []}

        entities[cik]["quarters"].append(
            {
                "filename": report["filename"],
                "quarter": report["quarter"],
                "filing_date": report["filing_date"],
            }
        )

    # 按季度排序
    for entity in entities.values():
        entity["quarters"].sort(key=lambda x: x["filing_date"], reverse=True)

    return jsonify({"entities": list(entities.values())})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
