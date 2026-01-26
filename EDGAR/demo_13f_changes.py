#!/usr/bin/env python3
"""
演示13F持仓变化显示 - Berkshire Hathaway (BRK.B) 案例
"""

import sys

sys.path.insert(0, "/Users/wonderer/Desktop/Project/EDGAR")

from view_13f_holdings import HoldingsViewer
from rich.console import Console

console = Console()


def demo_berkshire():
    """演示Berkshire Hathaway的持仓变化"""

    console.print("\n[bold cyan]=" * 50)
    console.print("[bold cyan]13F 持仓变化分析演示")
    console.print("[bold cyan]标的: Berkshire Hathaway (Ticker: B)")
    console.print("[bold cyan]=" * 50 + "\n")

    viewer = HoldingsViewer()

    # 加载报告
    if not viewer.load_reports():
        console.print("[red]无法加载报告[/red]")
        return

    ticker = "B"
    if ticker not in viewer.reports:
        console.print(f"[red]未找到 {ticker} 的报告[/red]")
        return

    dates = sorted(viewer.reports[ticker].keys())
    console.print(f"[green]✓ 找到 {len(dates)} 期13F报告:[/green]")
    for i, date in enumerate(dates, 1):
        console.print(f"  {i}. {date}")
    console.print()

    # 显示最近两期的持仓变化
    if len(dates) >= 2:
        console.print("[bold yellow]━" * 50)
        console.print(f"[bold yellow]季度对比: {dates[-2]} → {dates[-1]}")
        console.print("[bold yellow]━" * 50 + "\n")

        # 显示前30个持仓的变化
        viewer.display_detailed_holdings(ticker, dates[-2:], limit=30)

        console.print("\n[bold green]功能说明:")
        console.print("[green]• 🆕 = 新建仓位 (绿色背景)")
        console.print("[green]• ↑ = 增持 (绿色背景)")
        console.print("[red]• ↓ = 减持 (暗红色背景)")
        console.print("[dim]• — = 持股数未变化")
        console.print("[dim]• 股数变化 = 持股数量的绝对变化")
        console.print("[dim]• 变化% = 持股数量的百分比变化[/dim]\n")


if __name__ == "__main__":
    try:
        demo_berkshire()
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        import traceback

        traceback.print_exc()
