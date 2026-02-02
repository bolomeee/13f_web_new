#!/usr/bin/env python3
"""
爬虫功能测试脚本 (Crawler Test Script)

测试EDGAR爬虫服务是否能正常工作
Test if EDGAR crawler service works properly
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_config.settings")
django.setup()

from crawler.models import Institution
from crawler.edgar_service import EDGARCrawlerService
from crawler.services import InstitutionService


def test_crawler():
    """测试爬虫功能"""
    print("=" * 60)
    print("🧪 测试EDGAR爬虫服务")
    print("=" * 60)

    # 1. 创建或获取测试机构（Berkshire Hathaway）
    print("\n1️⃣ 准备测试机构...")
    institution_service = InstitutionService()
    institution = institution_service.get_or_create_institution(
        cik="0001067983", name="Berkshire Hathaway Inc"
    )
    print(f"   ✅ 机构: {institution.name}")
    print(f"   CIK: {institution.cik}")

    # 2. 初始化爬虫服务
    print("\n2️⃣ 初始化爬虫服务...")
    crawler = EDGARCrawlerService()
    print("   ✅ 爬虫服务已初始化")

    # 3. 测试获取文件列表
    print("\n3️⃣ 测试获取13F文件列表...")
    try:
        filings_list = crawler._get_13f_filings_list(institution.cik, max_count=2)
        print(f"   ✅ 找到 {len(filings_list)} 个13F文件")

        if filings_list:
            for i, filing in enumerate(filings_list, 1):
                print(f"\n   文件 {i}:")
                print(f"      - 文件编号: {filing['accession_number']}")
                print(f"      - 提交日期: {filing['filing_date']}")
                print(f"      - 报告日期: {filing['report_date']}")
    except Exception as e:
        print(f"   ❌ 获取文件列表失败: {e}")
        return False

    # 4. 测试完整爬取流程
    print("\n4️⃣ 测试完整爬取流程...")
    print("   ⚠️  这将下载真实的SEC数据，可能需要几分钟...")

    try:
        filings_count = crawler.crawl_institution_13f(
            institution=institution, max_filings=1  # 只爬取1个文件进行测试
        )

        print(f"\n   ✅ 成功处理 {filings_count} 个文件")

        # 5. 验证数据
        print("\n5️⃣ 验证保存的数据...")

        # 检查Filing
        filings = institution.filings.all()
        print(f"   📄 申报文件数: {filings.count()}")

        if filings.exists():
            latest_filing = filings.first()
            print(f"   最新文件: {latest_filing.quarter}")
            print(f"   报告期: {latest_filing.period_of_report}")

            # 检查Holdings
            holdings = latest_filing.holdings.all()
            print(f"   📊 持仓记录数: {holdings.count()}")

            if holdings.exists():
                print("\n   前5个持仓:")
                for holding in holdings[:5]:
                    print(f"      - {holding.ticker}: {holding.share_count:,} 股")
                    print(f"        市值: ${holding.value:,.2f}")
                    print(f"        操作: {holding.action_type or 'N/A'}")

            # 检查Options
            options = latest_filing.option_positions.all()
            print(f"\n   📈 期权记录数: {options.count()}")

            if options.exists():
                print("   期权持仓:")
                for option in options[:5]:
                    print(
                        f"      - {option.ticker} {option.option_type}: {option.contracts} 合约"
                    )

        print("\n" + "=" * 60)
        print("✅ 爬虫测试完成!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n   ❌ 爬取失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_crawler()
    sys.exit(0 if success else 1)
