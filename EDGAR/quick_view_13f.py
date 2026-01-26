#!/usr/bin/env python3
"""
13F 持仓数据快速查看脚本

非交互模式，通过命令行参数快速查看指定的 13F 持仓数据

使用示例:
    python quick_view_13f.py --ticker B --date latest --top 10
    python quick_view_13f.py --ticker B --compare all
    python quick_view_13f.py --ticker B --date 2024-11-14 --detail 30
"""

import argparse
import sys
from pathlib import Path

# 导入主查看器
from view_13f_holdings import HoldingsViewer, console


def quick_view(
    ticker: str,
    date_option: str = "latest",
    top_n: int = 10,
    detail_limit: int = 0,
    compare: bool = False,
):
    """快速查看模式"""

    viewer = HoldingsViewer()

    # 加载报告
    console.print(f"[cyan]📂 加载 13F 报告...[/cyan]")
    if not viewer.load_reports():
        return

    # 检查 ticker
    if ticker not in viewer.reports:
        console.print(f"[red]❌ 未找到 Ticker: {ticker}[/red]")
        console.print("\n[yellow]可用的 Ticker:[/yellow]")
        for t in viewer.reports.keys():
            console.print(f"  - {t}")
        return

    # 确定日期
    available_dates = sorted(viewer.reports[ticker].keys())

    if date_option == "latest":
        dates = [available_dates[-1]]
    elif date_option == "all":
        dates = available_dates
    elif date_option in available_dates:
        dates = [date_option]
    else:
        console.print(f"[red]❌ 无效的日期选项: {date_option}[/red]")
        console.print(f"\n[yellow]可用日期:[/yellow] {', '.join(available_dates)}")
        return

    console.print()

    # 显示汇总
    viewer.display_summary(ticker, dates)

    # 显示 Top N
    if top_n > 0:
        viewer.display_top_holdings(ticker, dates, top_n=top_n)

    # 显示详细持仓
    if detail_limit > 0:
        viewer.display_detailed_holdings(ticker, dates, limit=detail_limit)

    # 显示对比
    if compare and len(dates) > 1:
        viewer.compare_periods(ticker, dates)


def main():
    parser = argparse.ArgumentParser(
        description="13F 持仓数据快速查看工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --ticker B --date latest --top 10
  %(prog)s --ticker B --date 2024-11-14 --detail 50
  %(prog)s --ticker B --compare all
  %(prog)s --ticker B --date all --top 5 --compare
        """,
    )

    parser.add_argument("--ticker", "-t", required=True, help="要查看的 Ticker")
    parser.add_argument(
        "--date",
        "-d",
        default="latest",
        help="日期选项: latest, all, 或具体日期 (默认: latest)",
    )
    parser.add_argument(
        "--top", type=int, default=10, help="显示 Top N 持仓 (默认: 10, 设为 0 不显示)"
    )
    parser.add_argument(
        "--detail", type=int, default=0, help="显示详细持仓数量 (默认: 0 不显示)"
    )
    parser.add_argument(
        "--compare", action="store_true", help="显示多期对比 (需要多个日期)"
    )

    args = parser.parse_args()

    try:
        quick_view(
            ticker=args.ticker,
            date_option=args.date,
            top_n=args.top,
            detail_limit=args.detail,
            compare=args.compare,
        )
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  用户中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 错误: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
