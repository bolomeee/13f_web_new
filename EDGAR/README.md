# EDGAR 财报与持仓数据下载器

本项目提供一个强大且易于使用的工具，用于从美国证券交易委员会（SEC）的EDGAR数据库下载：
- **10-K 年度报告**：上市公司的年度财务报告
- **13F-HR 持仓报告**：机构投资者的季度持仓明细

该工具能够高效处理现代iXBRL格式的10-K文档和XML格式的13F信息表，并生成高质量、结构化、适合AI模型分析的JSON格式数据。

## 核心功能

### 10-K 年报功能
- **多公司批量下载**: 在配置文件中通过股票代码（Ticker）指定一个或多个公司。
- **灵活的年份选择**: 支持指定单个年份（如 "2023"）或一个年份区间（如 "2020-2023"）。
- **智能HTML解析**:
    - 采用先进的"内容块"提取策略，准确地从复杂的iXBRL文档中识别并抓取19个标准`ITEM`章节的完整内容。
    - 自动清理HTML标签、样式和脚本，只保留纯净的文本。
    - 内置行级去重逻辑，有效清除财务报表中常见的重复文本行。
- **结构化JSON输出**:
    - 为每份报告生成一个独立的JSON文件。
    - JSON文件包含清晰的文档元数据、按`ITEM`组织的文本内容、以及结构化的财务表格。

### 13F-HR 持仓报告功能（新增）
- **机构投资者持仓追踪**: 下载并解析机构投资者的季度持仓报告。
- **完整持仓明细**: 提取每个持仓的发行人名称、CUSIP、市值、股数等详细信息。
- **投票权信息**: 包含独占、共享和无投票权的详细分布。
- **投资决策权**: 记录每个持仓的投资决策权类型（SOLE/SHARED/OTHER）。
- **自动统计分析**: 
    - 计算总持仓数量和总市值
    - 生成前10大持仓排名
    - 分析投资决策权分布

### 通用功能
- **CIK自动映射与缓存**: 自动将股票代码映射为SEC所需的CIK编号，并缓存结果（`ticker_cik_cache.json`）以提高后续运行速度。
- **详细日志**: 记录详细的运行日志到 `edgar_downloader.log`，便于追踪和调试。

## 如何使用

### 1. 环境设置

首先，确保你已经安装了Python 3，然后通过`pip`安装所有必需的依赖库：

```bash
pip install -r requirements.txt
```

### 2. 参数配置

在运行脚本之前，请根据你的需求修改 `config.json` 文件：

#### 下载 10-K 年报示例：
```json
{
  "form_type": "10-K",
  "companies": {
    "tickers": "LMT,GOOGL,MSFT",
    "description": "需要下载的股票代码，用逗号分隔。"
  },
  "download_settings": {
    "year_range": "2022-2023",
    "download_directory": "SEC_Filings",
    "description": "年份范围支持 '2023' (单年) 或 '2020-2023' (包含起止年份的区间)。"
  },
  "conversion_settings": {
    "enable_json_conversion": true,
    "json_output_directory": "JSON_Reports",
    "description": "是否启用JSON转换以及输出目录。"
  },
  "user_agent": {
    "email": "your_email@example.com",
    "description": "请替换为你的真实邮箱地址，这是SEC的要求。"
  }
}
```

#### 下载 13F-HR 持仓报告示例：
```json
{
  "form_type": "13F-HR",
  "companies": {
    "tickers": "BRK.B",
    "description": "机构投资者代码。BRK.B=Berkshire Hathaway, JPM=JPMorgan Chase等"
  },
  "download_settings": {
    "year_range": "2024",
    "download_directory": "SEC_Filings",
    "description": "13F是季度报告，年份范围会下载该年度所有季度的报告。"
  },
  "conversion_settings": {
    "enable_json_conversion": true,
    "json_output_directory": "JSON_Reports"
  },
  "user_agent": {
    "email": "your_email@example.com"
  }
}
```

> **重要提示**: 请务必将 `user_agent.email` 修改为你的真实电子邮件地址，以便合规地访问SEC的服务器。

### 3. 运行脚本

配置完成后，直接运行主脚本：

```bash
python edgar_downloader.py
```

脚本将自动开始下载、解析和转换过程。

### 4. 查看 13F 持仓数据（新增）

下载完成后，可以使用精美的 Rich 界面查看器来分析 13F 持仓数据：

#### 交互式查看器

```bash
python view_13f_holdings.py
```

功能特点：
- 🎨 精美的表格展示
- 📈 多期数据对比
- 🔍 交互式选择 Ticker 和日期
- 📈 Top 持仓排名
- 📊 详细持仓列表
- 📊 **持仓变化追踪**（新）：
  - 🆕 新建仓位标记（绿色背景高亮）
  - ↑ 增持标记（绿色背景高亮，基于持股数增加）
  - ↓ 减持标记（暗红色背景高亮，基于持股数减少）
  - — 持平标记（持股数未变化）
  - � 显示上期/本期持股数对比
  - 📈 显示股数变化的绝对数量和百分比
  - 📊 变化统计摘要（新建/增持/减持的公司数量及总股数）

#### 快速演示持仓变化（推荐）

```bash
# 演示Berkshire Hathaway的季度持仓变化（含颜色高亮）
python demo_13f_changes.py
```

#### 快速查看工具

```bash
# 查看最新一期的 Top 10 持仓
python quick_view_13f.py --ticker B --date latest --top 10

# 查看所有时期并对比
python quick_view_13f.py --ticker B --date all --top 5 --compare

# 查看详细持仓
python quick_view_13f.py --ticker B --date 2024-11-14 --detail 50
```

详细使用说明请参阅 [`13F_VIEWER_GUIDE.md`](13F_VIEWER_GUIDE.md)。

## 输出说明

脚本运行后，你会得到两类输出：

1.  **原始文件**: 存放在 `config.json` 中 `download_directory` 指定的目录下（默认为 `SEC_Filings/`）。
    - 10-K: HTML格式文件
    - 13F-HR: XML格式文件
2.  **结构化JSON文件**: 存放在 `config.json` 中 `json_output_directory` 指定的目录下（默认为 `JSON_Reports/`）。

### 10-K JSON文件结构概览

每个10-K JSON文件都包含以下顶级键：

- `document_metadata`: 文档元数据，包括公司名称、股票代码、CIK、财年、归档日期等。
- `sec_sections`: 核心内容，一个以`item_1`, `item_1a`等为键的字典，每个键对应一个包含标题、纯文本内容、字数统计等信息的对象。
- `financial_tables`: 从文档中提取的所有表格，每个表格都结构化为表头（headers）和数据行（data）。
- `xbrl_data`: 提取到的XBRL财务标签数据。
- `processing_stats`: 处理过程的统计信息，如提取到的章节数、文本总长度等。

### 13F-HR JSON文件结构概览

每个13F-HR JSON文件都包含以下顶级键：

- `document_metadata`: 文档元数据，包括申报机构名称、CIK、报告期、归档日期等。
- `holdings`: 持仓明细数组，每个持仓包含：
  - `issuer_name`: 发行公司名称
  - `cusip`: 证券CUSIP码（9位唯一标识符）
  - `value_usd`: 持仓市值（美元，2023年1月3日后的新规则）
  - `shares_or_principal`: 股数或本金金额
  - `investment_discretion`: 投资决策权（SOLE/SHARED/DFND）
  - `voting_authority`: 投票权分布（sole/shared/none）
  - `price_per_share_estimated`: 估算的每股价格（基于市值/股数）
- `summary_statistics`: 汇总统计信息
  - `total_positions`: 总持仓数量
  - `total_value_usd`: 总市值（美元）
  - `average_position_value_usd`: 平均持仓价值
  - `top_10_holdings`: 前10大持仓及其占比
  - `investment_discretion_distribution`: 投资决策权分布
- `extraction_info`: 提取过程的元信息

> **注意**: SEC 于 2023年1月3日 起将 13F 表单中的 value 字段单位从「千美元」改为「美元」，本工具已适配此变更。

## 应用场景

这个结构化的输出使得AI模型可以轻松地进行各种分析，例如：

### 10-K 分析场景
- 跨年度的财务指标对比
- 特定风险因素（Item 1A）的语义分析和演变追踪
- 管理层讨论与分析（Item 7）的关键主题提取
- 自动化生成公司摘要

### 13F-HR 分析场景
- 追踪顶级投资者的持仓变化
- 分析机构投资者的行业配置
- 识别"聪明钱"的投资趋势
- 构建跟随策略和投资组合
- 分析投票权和公司治理影响

## 技术架构

- `edgar_downloader.py`: 主下载器，支持10-K和13F-HR两种表单类型
- `sec_13f_extractor.py`: 专门的13F XML解析器
- `SECStandardExtractor`: 内置的10-K HTML/iXBRL解析器
- `test_13f_extractor.py`: 13F提取器测试套件

## 测试

运行 13F 提取器测试套件：

```bash
python test_13f_extractor.py
```

测试内容包括：
1. **基本初始化测试** - 验证提取器初始化
2. **XML文件提取测试** - 验证XML解析能力
3. **数据质量测试** - 验证持仓数据完整性
4. **Value字段解释测试** - 验证价值计算正确性
5. **统计计算测试** - 验证统计信息准确性
6. **已知持仓验证** - 验证已知CUSIP匹配
7. **JSON文件对比** - 验证输出文件结构

## 版本历史

- **v3.1** (2026-01-25): 修复13F value字段单位问题（适配SEC 2023年规则变更），添加测试套件
- **v3.0** (2026-01): 新增13F-HR持仓报告支持
- **v2.2** (2025-12): 优化10-K解析逻辑
- **v1.0** (2025-01): 初始版本，支持10-K下载

## 许可证

MIT License
