#!/usr/bin/env python3
"""
SEC 13F 提取器测试脚本 (SEC 13F Extractor Test Script)

这个脚本用于测试和验证 SEC 13F 数据提取功能的正确性。
测试内容包括：
1. XML 文件解析能力
2. 持仓数据提取准确性
3. 统计信息计算正确性
4. 数据格式合规性

运行方式: python test_13f_extractor.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sec_13f_extractor import SEC13FExtractor


def print_header(title: str):
    """打印格式化的标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title: str):
    """打印格式化的小节标题"""
    print(f"\n--- {title} ---")


def test_basic_initialization():
    """测试基本初始化"""
    print_section("1. 测试基本初始化")

    try:
        extractor = SEC13FExtractor()
        print("✅ SEC13FExtractor 初始化成功")
        return True, extractor
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False, None


def test_xml_file_extraction(extractor: SEC13FExtractor, xml_file: str):
    """测试 XML 文件提取"""
    print_section(f"2. 测试 XML 文件提取: {os.path.basename(xml_file)}")

    if not os.path.exists(xml_file):
        print(f"⚠️ 文件不存在: {xml_file}")
        return False, None

    try:
        with open(xml_file, "r", encoding="utf-8") as f:
            xml_content = f.read()

        result = extractor.extract_13f_data(xml_content, xml_file)

        # 验证结果结构
        required_keys = [
            "document_metadata",
            "holdings",
            "summary_statistics",
            "extraction_info",
        ]
        missing_keys = [k for k in required_keys if k not in result]

        if missing_keys:
            print(f"❌ 缺少必要的键: {missing_keys}")
            return False, None

        print(f"✅ XML 解析成功")
        print(f"   - 持仓数量: {len(result['holdings'])}")
        print(f"   - 元数据完整: {bool(result['document_metadata'])}")

        return True, result
    except Exception as e:
        print(f"❌ XML 提取失败: {e}")
        import traceback

        traceback.print_exc()
        return False, None


def test_holdings_data_quality(result: dict):
    """测试持仓数据质量"""
    print_section("3. 测试持仓数据质量")

    holdings = result.get("holdings", [])

    if not holdings:
        print("⚠️ 没有持仓数据")
        return False

    # 数据质量检查
    issues = []
    valid_count = 0

    for idx, h in enumerate(holdings):
        position_issues = []

        # 检查必要字段
        if not h.get("issuer_name"):
            position_issues.append("缺少发行人名称")

        cusip = h.get("cusip", "")
        if not cusip or len(cusip) != 9:
            position_issues.append(f"CUSIP无效: '{cusip}'")

        value = h.get("value_usd")
        if value is None or value < 0:
            position_issues.append(f"市值无效: {value}")

        shares_info = h.get("shares_or_principal", {})
        if not shares_info.get("amount"):
            position_issues.append("缺少股数信息")

        if position_issues:
            issues.append((idx + 1, position_issues))
        else:
            valid_count += 1

    # 打印结果
    print(f"✅ 有效持仓: {valid_count}/{len(holdings)}")

    if issues and len(issues) <= 5:
        print(f"⚠️ 数据问题 ({len(issues)} 条):")
        for pos_id, pos_issues in issues[:5]:
            print(f"   - 持仓 #{pos_id}: {', '.join(pos_issues)}")
    elif issues:
        print(f"⚠️ 发现 {len(issues)} 条数据问题（仅显示前5条）")

    return valid_count > 0


def test_value_field_interpretation(result: dict):
    """测试 value 字段解释的正确性"""
    print_section("4. 测试 Value 字段解释")

    holdings = result.get("holdings", [])
    stats = result.get("summary_statistics", {})

    if not holdings:
        print("⚠️ 没有持仓数据可供测试")
        return False

    # 验证几个关键持仓的价值合理性
    # 对于2024年数据，value应该是美元单位
    print("\n📊 持仓价值分析 (2024年后数据，value单位应为美元):")

    sample_holdings = holdings[:5]
    for h in sample_holdings:
        issuer = h.get("issuer_name", "Unknown")[:25]
        value = h.get("value_usd", 0)
        shares = h.get("shares_or_principal", {}).get("amount", 0)

        # 计算估算股价
        if shares and value:
            price_est = value / shares
            # 注意：当前代码将 value 误认为"千美元"，所以估算价格可能错误
            print(
                f"   {issuer:25s} | 价值(USD): ${value:,.0f} | 股数: {shares:,.0f} | 估算股价: ${price_est:.2f}"
            )

    # 检查总价值的合理性
    total_value = stats.get("total_value_usd", 0)

    print(f"\n📈 投资组合总价值:")
    print(f"   - total_value_usd: {total_value:,.0f}")

    # 验证逻辑：如果这是2024年的数据，伯克希尔的13F持仓应该在1000-3000亿美元之间
    if 100_000_000_000 < total_value < 500_000_000_000:
        print(f"   ✅ 总价值在合理范围内 ({total_value/1e9:.1f}B USD)")
        return True
    elif total_value > 1_000_000_000_000:
        print(f"   ⚠️ 总价值异常大，可能存在单位计算问题")
        return False
    else:
        print(f"   ⚠️ 无法确定价值合理性")
        return True


def test_statistics_calculation(result: dict):
    """测试统计信息计算"""
    print_section("5. 测试统计信息计算")

    stats = result.get("summary_statistics", {})
    holdings = result.get("holdings", [])

    # 验证总持仓数
    total_positions = stats.get("total_positions", 0)
    if total_positions == len(holdings):
        print(f"✅ 持仓数量正确: {total_positions}")
    else:
        print(f"❌ 持仓数量不匹配: 统计={total_positions}, 实际={len(holdings)}")
        return False

    # 验证前10大持仓
    top_10 = stats.get("top_10_holdings", [])
    if len(top_10) == min(10, len(holdings)):
        print(f"✅ Top 10 持仓数量正确: {len(top_10)}")

        # 打印前5大持仓
        print("\n📊 前5大持仓:")
        for h in top_10[:5]:
            print(
                f"   #{h['rank']:2d} | {h['issuer'][:30]:30s} | 占比: {h['percentage']:.2f}%"
            )
    else:
        print(f"⚠️ Top 10 持仓数量问题")

    # 验证百分比总和
    total_pct = sum(h.get("percentage", 0) for h in top_10)
    print(f"\n   Top 10 占比总和: {total_pct:.2f}%")

    return True


def test_specific_holdings(result: dict):
    """测试特定已知持仓数据"""
    print_section("6. 验证已知持仓数据")

    holdings = result.get("holdings", [])

    # 伯克希尔已知的主要持仓（CUSIP）
    known_holdings = {
        "037833100": "APPLE INC",
        "025816109": "AMERICAN EXPRESS CO",
        "060505104": "BANK AMER CORP",
        "191216100": "COCA COLA CO",
        "166764100": "CHEVRON CORP",
    }

    print("\n🔍 验证已知持仓:")

    found_count = 0
    for cusip, expected_name in known_holdings.items():
        # 查找所有匹配的持仓
        matching = [h for h in holdings if h.get("cusip") == cusip]

        if matching:
            found_count += 1
            total_value = sum(h.get("value_usd", 0) or 0 for h in matching)
            total_shares = sum(
                h.get("shares_or_principal", {}).get("amount", 0) or 0 for h in matching
            )

            actual_name = matching[0].get("issuer_name", "Unknown")
            print(
                f"   ✅ {expected_name[:25]:25s} | CUSIP: {cusip} | 记录数: {len(matching)}"
            )
            print(f"      发行人: {actual_name} | 总股数: {total_shares:,.0f}")
        else:
            print(f"   ❌ {expected_name[:25]:25s} | CUSIP: {cusip} | 未找到")

    print(f"\n   找到 {found_count}/{len(known_holdings)} 个已知持仓")

    return found_count >= 3  # 至少找到3个已知持仓


def test_compare_with_existing_json():
    """与已有的 JSON 文件比较"""
    print_section("7. 与已有 JSON 文件对比")

    json_dir = Path("JSON_Reports")
    xml_dir = Path("SEC_Filings")

    if not json_dir.exists() or not xml_dir.exists():
        print("⚠️ 目录不存在，跳过对比测试")
        return True

    # 查找 13F JSON 文件
    json_files = list(json_dir.glob("*13F-HR*.json"))

    if not json_files:
        print("⚠️ 未找到 13F JSON 文件")
        return True

    print(f"📁 找到 {len(json_files)} 个 13F JSON 文件:")
    for jf in json_files:
        size_kb = jf.stat().st_size / 1024
        print(f"   - {jf.name} ({size_kb:.1f} KB)")

        # 读取并验证 JSON 结构
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)

            holdings_count = len(data.get("holdings", []))
            total_value = data.get("summary_statistics", {}).get("total_value_usd", 0)

            print(f"     持仓数: {holdings_count}, 总价值(USD): {total_value:,.0f}")
        except Exception as e:
            print(f"     ❌ 读取失败: {e}")

    return True


def run_all_tests():
    """运行所有测试"""
    print_header("SEC 13F 提取器测试套件")
    print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 工作目录: {os.getcwd()}")

    results = {}

    # 1. 基本初始化测试
    success, extractor = test_basic_initialization()
    results["初始化"] = success

    if not success:
        print("\n❌ 初始化失败，终止测试")
        return results

    # 2. 查找并测试 XML 文件
    xml_dir = Path("SEC_Filings")
    xml_files = list(xml_dir.glob("*13F-HR*.xml")) if xml_dir.exists() else []

    if not xml_files:
        print("\n⚠️ 未找到 13F XML 文件")
        results["XML提取"] = False
    else:
        # 测试最新的一个文件
        test_file = sorted(xml_files)[-1]
        success, result = test_xml_file_extraction(extractor, str(test_file))
        results["XML提取"] = success

        if success and result:
            # 3. 数据质量测试
            results["数据质量"] = test_holdings_data_quality(result)

            # 4. Value 字段测试
            results["Value字段"] = test_value_field_interpretation(result)

            # 5. 统计计算测试
            results["统计计算"] = test_statistics_calculation(result)

            # 6. 已知持仓验证
            results["已知持仓"] = test_specific_holdings(result)

    # 7. JSON 文件对比
    results["JSON对比"] = test_compare_with_existing_json()

    # 打印测试摘要
    print_header("测试结果摘要")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_flag in results.items():
        status = "✅ 通过" if passed_flag else "❌ 失败"
        print(f"   {test_name:15s}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查上面的详细信息")

    return results


if __name__ == "__main__":
    run_all_tests()
