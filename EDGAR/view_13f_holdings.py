#!/usr/bin/env python3
"""
13F 持仓数据可视化查看器 (13F Holdings Viewer)

使用 Rich 库美化的交互式命令行界面，用于查看和分析 13F-HR 持仓报告。

功能特点:
- 🎨 精美的表格展示
- 📊 多期数据对比
- 🔍 按 Ticker 筛选
- 📈 Top 持仓排名
- 💰 市值和变动分析

运行方式: python view_13f_holdings.py
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.text import Text
from rich.align import Align

console = Console()


class HoldingsViewer:
    """13F 持仓数据查看器"""

    def __init__(self, json_dir: str = "JSON_Reports"):
        self.json_dir = Path(json_dir)
        self.reports = {}  # {ticker: {date: report_data}}

    def load_reports(self):
        """加载所有 13F JSON 报告"""
        if not self.json_dir.exists():
            console.print(f"[red]❌ 目录不存在: {self.json_dir}[/red]")
            return False

        json_files = list(self.json_dir.glob("*13F-HR*.json"))

        if not json_files:
            console.print(f"[yellow]⚠️  未找到 13F-HR JSON 文件[/yellow]")
            return False

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("📂 加载 13F 报告...", total=len(json_files))

            for json_file in json_files:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # 提取元数据
                    metadata = data.get("document_metadata", {})
                    ticker = metadata.get("ticker", "UNKNOWN")
                    filing_date = metadata.get("filing_date", "UNKNOWN")

                    # 组织数据
                    if ticker not in self.reports:
                        self.reports[ticker] = {}

                    self.reports[ticker][filing_date] = data

                except Exception as e:
                    console.print(f"[red]❌ 读取失败: {json_file.name} - {e}[/red]")

                progress.update(task, advance=1)

        console.print(f"[green]✅ 成功加载 {len(json_files)} 个报告文件[/green]")
        return True

    def show_available_tickers(self):
        """显示可用的 Ticker 列表"""
        if not self.reports:
            console.print("[yellow]⚠️  没有可用的报告数据[/yellow]")
            return

        table = Table(
            title="📋 可用的 13F 报告",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("序号", style="dim", width=6)
        table.add_column("Ticker", style="bold green", width=12)
        table.add_column("报告数量", justify="right", style="yellow")
        table.add_column("日期范围", style="blue")

        for idx, (ticker, reports) in enumerate(sorted(self.reports.items()), 1):
            dates = sorted(reports.keys())
            date_range = f"{dates[0]} ~ {dates[-1]}" if len(dates) > 1 else dates[0]

            table.add_row(str(idx), ticker, str(len(reports)), date_range)

        console.print(table)

    def select_ticker(self) -> Optional[str]:
        """交互式选择 Ticker"""
        self.show_available_tickers()

        console.print()
        ticker = Prompt.ask(
            "[bold cyan]请输入要查看的 Ticker[/bold cyan]",
            default=list(self.reports.keys())[0] if self.reports else None,
        )

        if ticker not in self.reports:
            console.print(f"[red]❌ 未找到 Ticker: {ticker}[/red]")
            return None

        return ticker

    def select_dates(self, ticker: str) -> List[str]:
        """交互式选择日期范围"""
        available_dates = sorted(self.reports[ticker].keys())

        console.print(f"\n[bold cyan]📅 {ticker} 可用的报告日期:[/bold cyan]")
        for idx, date in enumerate(available_dates, 1):
            console.print(f"  {idx}. {date}")

        console.print()
        choice = Prompt.ask(
            "[bold cyan]选择查看方式[/bold cyan]",
            choices=["all", "latest", "range", "single"],
            default="latest",
        )

        if choice == "all":
            return available_dates
        elif choice == "latest":
            return [available_dates[-1]]
        elif choice == "single":
            idx = int(Prompt.ask("选择日期编号", default="1")) - 1
            return [available_dates[idx]]
        else:  # range
            start_idx = int(Prompt.ask("起始日期编号", default="1")) - 1
            end_idx = (
                int(Prompt.ask("结束日期编号", default=str(len(available_dates)))) - 1
            )
            return available_dates[start_idx : end_idx + 1]

    def display_summary(self, ticker: str, dates: List[str]):
        """显示持仓汇总信息"""
        console.print("\n" + "=" * 100)
        console.print()

        # 创建汇总面板
        for date in dates:
            report = self.reports[ticker][date]
            metadata = report["document_metadata"]
            stats = report["summary_statistics"]

            # 构建信息文本
            info_lines = [
                f"[bold cyan]📊 {ticker} - 13F-HR 持仓报告[/bold cyan]",
                "",
                f"[yellow]📅 申报日期:[/yellow] {date}",
                f"[yellow]🏢 申报机构:[/yellow] {metadata.get('filing_manager', 'Unknown')}",
                f"[yellow]📍 CIK:[/yellow] {metadata.get('cik', 'Unknown')}",
                f"[yellow]📊 报告期:[/yellow] {metadata.get('report_period', 'Unknown')}",
                "",
                f"[green]💼 总持仓数量:[/green] {stats.get('total_positions', 0):,}",
                f"[green]💰 总市值:[/green] ${stats.get('total_value_usd', 0):,.0f} ({stats.get('total_value_usd', 0)/1e9:.2f}B)",
                f"[green]📈 平均持仓价值:[/green] ${stats.get('average_position_value_usd', 0):,.0f}",
            ]

            panel = Panel(
                "\n".join(info_lines),
                border_style="blue",
                padding=(1, 2),
            )

            console.print(panel)
            console.print()

    def display_top_holdings(self, ticker: str, dates: List[str], top_n: int = 10):
        """显示 Top N 持仓"""
        for date in dates:
            report = self.reports[ticker][date]
            stats = report["summary_statistics"]
            top_holdings = stats.get("top_10_holdings", [])[:top_n]

            if not top_holdings:
                console.print(f"[yellow]⚠️  {date} 没有持仓数据[/yellow]")
                continue

            table = Table(
                title=f"🏆 Top {top_n} 持仓 - {date}",
                box=box.DOUBLE_EDGE,
                show_header=True,
                header_style="bold magenta",
            )

            table.add_column("排名", justify="center", style="cyan", width=6)
            table.add_column("发行人", style="bold white", width=35)
            table.add_column("CUSIP", style="dim", width=12)
            table.add_column("市值 (USD)", justify="right", style="green", width=18)
            table.add_column("占比 (%)", justify="right", style="yellow", width=10)

            for holding in top_holdings:
                rank_style = "bold red" if holding["rank"] <= 3 else "cyan"

                table.add_row(
                    f"#{holding['rank']}",
                    holding["issuer"][:35],
                    holding["cusip"],
                    f"${holding['value_usd']:,.0f}",
                    f"{holding['percentage']:.2f}%",
                    style=rank_style if holding["rank"] <= 3 else None,
                )

            console.print(table)
            console.print()

    def display_detailed_holdings(self, ticker: str, dates: List[str], limit: int = 50):
        """显示详细持仓信息（含季度变化分析）"""
        # 如果只有一期数据，使用简化版本
        if len(dates) == 1:
            self._display_single_period_holdings(ticker, dates[0], limit)
            return

        # 多期数据：显示带变化分析的版本
        self._display_multi_period_holdings(ticker, dates, limit)

    def _display_single_period_holdings(self, ticker: str, date: str, limit: int):
        """显示单期持仓信息"""
        report = self.reports[ticker][date]
        holdings = report.get("holdings", [])

        if not holdings:
            console.print(f"[yellow]⚠️  {date} 没有持仓数据[/yellow]")
            return

        # 按市值排序并合并同一CUSIP的持仓
        cusip_holdings = self._merge_holdings_by_cusip(holdings)
        merged_holdings = sorted(
            cusip_holdings.values(), key=lambda x: x["value_usd"], reverse=True
        )
        display_holdings = merged_holdings[:limit]

        table = Table(
            title=f"📋 详细持仓 - {date} (显示前 {limit} / 共 {len(merged_holdings)})",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold blue",
        )

        table.add_column("#", justify="center", style="dim", width=5)
        table.add_column("发行人", style="white", width=30)
        table.add_column("CUSIP", style="cyan", width=11)
        table.add_column("市值 (USD)", justify="right", style="green", width=16)
        table.add_column("股数", justify="right", style="yellow", width=14)
        table.add_column("估算股价", justify="right", style="magenta", width=12)

        for idx, h in enumerate(display_holdings, 1):
            table.add_row(
                str(idx),
                h["issuer_name"][:30],
                h["cusip"],
                f"${h['value_usd']:,.0f}",
                f"{h['shares']:,.0f}",
                f"${h['price']:.2f}",
            )

        console.print(table)
        console.print()

    def _merge_holdings_by_cusip(self, holdings: List[Dict]) -> Dict[str, Dict]:
        """合并同一CUSIP的持仓"""
        cusip_holdings = {}
        for h in holdings:
            cusip = h.get("cusip", "UNKNOWN")
            if cusip not in cusip_holdings:
                cusip_holdings[cusip] = {
                    "cusip": cusip,
                    "issuer_name": h.get("issuer_name", "Unknown"),
                    "value_usd": 0,
                    "shares": 0,
                    "price": h.get("price_per_share_estimated", 0) or 0,
                }

            cusip_holdings[cusip]["value_usd"] += h.get("value_usd", 0) or 0
            cusip_holdings[cusip]["shares"] += (
                h.get("shares_or_principal", {}).get("amount", 0) or 0
            )

        return cusip_holdings

    def _display_multi_period_holdings(self, ticker: str, dates: List[str], limit: int):
        """显示多期持仓变化对比（基于持股数）"""
        # 收集所有期的数据
        all_periods = {}
        for date in dates:
            report = self.reports[ticker][date]
            holdings = report.get("holdings", [])
            all_periods[date] = self._merge_holdings_by_cusip(holdings)

        # 使用最新一期的持仓作为基准
        latest_date = dates[-1]
        latest_holdings = all_periods[latest_date]

        # 如果有前一期，计算变化
        previous_date = dates[-2] if len(dates) >= 2 else None
        previous_holdings = all_periods.get(previous_date, {}) if previous_date else {}

        # 合并所有CUSIP（包括已关闭的持仓）
        all_cusips = set(latest_holdings.keys()) | set(previous_holdings.keys())

        # 计算变化并分类（基于持股数）
        holdings_with_changes = []
        for cusip in all_cusips:
            current = latest_holdings.get(cusip)
            previous = previous_holdings.get(cusip)

            current_shares = current["shares"] if current else 0
            previous_shares = previous["shares"] if previous else 0
            change_shares = current_shares - previous_shares

            # 计算变化百分比
            if previous_shares > 0:
                change_pct = (change_shares / previous_shares) * 100
            else:
                change_pct = 0

            # 分类：新建、增持、减持、清仓（基于股数）
            if previous_shares == 0 and current_shares > 0:
                change_type = "new"  # 新建仓位
            elif current_shares == 0:
                change_type = "closed"  # 清仓
            elif change_shares > 0:
                change_type = "increased"  # 增持
            elif change_shares < 0:
                change_type = "decreased"  # 减持
            else:
                change_type = "unchanged"  # 持平

            if current:  # 只显示当前仍持有的
                holdings_with_changes.append(
                    {
                        **current,
                        "previous_shares": previous_shares,
                        "change_shares": change_shares,
                        "change_pct": change_pct,
                        "change_type": change_type,
                    }
                )

        # 按当前持股数排序
        holdings_with_changes.sort(key=lambda x: x["shares"], reverse=True)
        display_holdings = holdings_with_changes[:limit]

        # 构建表格
        comparison_text = (
            f"{previous_date} → {latest_date}" if previous_date else latest_date
        )
        table = Table(
            title=f"📋 持仓变化分析 - {comparison_text} (显示前 {limit} / 共 {len(holdings_with_changes)})",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold blue",
        )

        table.add_column("#", justify="center", style="dim", width=4)
        table.add_column("发行人", style="white", width=30)
        table.add_column("上期持股", justify="right", style="cyan", width=14)
        table.add_column("本期持股", justify="right", style="green", width=14)
        table.add_column("变化", justify="center", width=6)
        table.add_column("股数变化", justify="right", style="yellow", width=15)
        table.add_column("变化%", justify="right", style="magenta", width=10)

        for idx, h in enumerate(display_holdings, 1):
            # 确定变化指示器和样式
            if h["change_type"] == "new":
                change_indicator = "🆕"
                row_style = "on #004d00"  # 深绿色背景
                change_text = f"+{abs(h['change_shares']):,.0f}"
                pct_text = "New"
            elif h["change_type"] == "increased":
                change_indicator = "↑"
                row_style = "on #004d00"  # 深绿色背景
                change_text = f"+{abs(h['change_shares']):,.0f}"
                pct_text = f"+{h['change_pct']:.1f}%"
            elif h["change_type"] == "decreased":
                change_indicator = "↓"
                row_style = "on #4d0000"  # 暗红色背景
                change_text = f"-{abs(h['change_shares']):,.0f}"
                pct_text = f"{h['change_pct']:.1f}%"
            else:
                change_indicator = "—"
                row_style = None
                change_text = "0"
                pct_text = "0%"

            # 渲染行
            table.add_row(
                str(idx),
                h["issuer_name"][:30],
                f"{h['previous_shares']:,.0f}",
                f"{h['shares']:,.0f}",
                change_indicator,
                change_text,
                pct_text,
                style=row_style,
            )

        console.print(table)

        # 显示统计摘要（基于股数）
        new_count = sum(1 for h in holdings_with_changes if h["change_type"] == "new")
        increased_count = sum(
            1 for h in holdings_with_changes if h["change_type"] == "increased"
        )
        decreased_count = sum(
            1 for h in holdings_with_changes if h["change_type"] == "decreased"
        )

        total_shares_increase = sum(
            h["change_shares"] for h in holdings_with_changes if h["change_shares"] > 0
        )
        total_shares_decrease = sum(
            abs(h["change_shares"])
            for h in holdings_with_changes
            if h["change_shares"] < 0
        )

        summary_text = (
            f"[green]🆕 新建: {new_count}  ↑ 增持: {increased_count}  "
            f"(+{total_shares_increase:,.0f} 股)[/green]  |  "
            f"[red]↓ 减持: {decreased_count}  (-{total_shares_decrease:,.0f} 股)[/red]"
        )

        console.print(Panel(summary_text, border_style="dim", padding=(0, 2)))
        console.print()

    def compare_periods(self, ticker: str, dates: List[str]):
        """对比多期持仓变化"""
        if len(dates) < 2:
            console.print("[yellow]⚠️  至少需要两期数据才能进行对比[/yellow]")
            return

        # 获取所有期的数据
        period_data = {}
        for date in dates:
            report = self.reports[ticker][date]
            stats = report["summary_statistics"]
            period_data[date] = {
                "total_positions": stats.get("total_positions", 0),
                "total_value": stats.get("total_value_usd", 0),
            }

        # 创建对比表格
        table = Table(
            title=f"📊 {ticker} 多期持仓对比",
            box=box.HEAVY_EDGE,
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("指标", style="bold white", width=20)
        for date in dates:
            table.add_column(date, justify="right", style="green", width=18)
        table.add_column("变化", justify="right", style="yellow", width=15)

        # 总持仓数对比
        row = ["持仓数量"]
        positions = [period_data[d]["total_positions"] for d in dates]
        row.extend([f"{p:,}" for p in positions])
        change = positions[-1] - positions[0]
        change_pct = (change / positions[0] * 100) if positions[0] > 0 else 0
        row.append(f"{change:+,} ({change_pct:+.1f}%)")
        table.add_row(*row)

        # 总市值对比
        row = ["总市值 (USD)"]
        values = [period_data[d]["total_value"] for d in dates]
        row.extend([f"${v:,.0f}" for v in values])
        change = values[-1] - values[0]
        change_pct = (change / values[0] * 100) if values[0] > 0 else 0
        row.append(f"${change:+,.0f} ({change_pct:+.1f}%)")
        table.add_row(*row)

        console.print(table)
        console.print()

    def run(self):
        """运行主程序"""
        # 显示欢迎信息
        welcome = Panel(
            Align.center(
                "[bold cyan]🏦 13F-HR 持仓数据查看器[/bold cyan]\n\n"
                "[dim]使用 Rich 美化的交互式持仓分析工具[/dim]",
                vertical="middle",
            ),
            border_style="bright_blue",
            padding=(1, 2),
        )
        console.print(welcome)
        console.print()

        # 加载报告
        if not self.load_reports():
            return

        console.print()

        # 主循环
        while True:
            # 选择 Ticker
            ticker = self.select_ticker()
            if not ticker:
                break

            # 选择日期
            dates = self.select_dates(ticker)
            if not dates:
                console.print("[red]❌ 没有选择有效的日期[/red]")
                continue

            # 显示汇总信息
            self.display_summary(ticker, dates)

            # 显示 Top 10 持仓
            self.display_top_holdings(ticker, dates, top_n=10)

            # 询问是否查看详细持仓
            if Confirm.ask("\n[cyan]是否查看详细持仓列表?[/cyan]", default=True):
                limit = int(Prompt.ask("[cyan]显示前多少个持仓?[/cyan]", default="50"))
                self.display_detailed_holdings(ticker, dates, limit=limit)

            # 如果是多期，询问是否对比
            if len(dates) > 1:
                if Confirm.ask("\n[cyan]是否查看多期对比?[/cyan]", default=True):
                    self.compare_periods(ticker, dates)

            console.print()

            # 询问是否继续
            if not Confirm.ask(
                "[bold cyan]是否继续查看其他报告?[/bold cyan]", default=False
            ):
                break

            console.print("\n" + "=" * 100 + "\n")

        # 结束信息
        console.print("\n[bold green]👋 感谢使用 13F 持仓数据查看器！[/bold green]\n")


def main():
    """主函数"""
    try:
        viewer = HoldingsViewer()
        viewer.run()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  用户中断程序[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 错误: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
