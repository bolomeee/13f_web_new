#!/usr/bin/env python3
"""
测试13F持仓变化显示功能
"""

import sys

sys.path.insert(0, "/Users/wonderer/Desktop/Project/EDGAR")

from view_13f_holdings import HoldingsViewer


def test_holdings_display():
    """测试持仓变化显示"""
    viewer = HoldingsViewer()

    # 加载报告
    if not viewer.load_reports():
        print("Failed to load reports")
        return

    # 对BRK-B进行测试
    ticker = "B"
    if ticker in viewer.reports:
        dates = sorted(viewer.reports[ticker].keys())
        print(f"\n找到 {ticker} 的 {len(dates)} 期报告: {dates}\n")

        # 测试多期对比（最后两期）
        if len(dates) >= 2:
            print("=" * 100)
            print("测试1: 显示最后两期的持仓变化")
            print("=" * 100)
            viewer.display_detailed_holdings(ticker, dates[-2:], limit=20)

        # 测试单期显示
        print("\n" + "=" * 100)
        print("测试2: 显示单期持仓")
        print("=" * 100)
        viewer.display_detailed_holdings(ticker, [dates[-1]], limit=10)

        # 测试所有期的对比
        if len(dates) >= 3:
            print("\n" + "=" * 100)
            print("测试3: 显示所有期的持仓变化（最后三期）")
            print("=" * 100)
            viewer.display_detailed_holdings(ticker, dates[-3:], limit=15)


if __name__ == "__main__":
    test_holdings_display()
