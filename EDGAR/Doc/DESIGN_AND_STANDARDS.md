# 系统设计与开发标准 (Design and Standards)

## 文档概述 (Document Overview)

**项目名称:** EDGAR HTML Data Cleansing and LLM Processing Pipeline  
**版本:** 1.0.0  
**系统架构师:** AI Assistant  
**创建日期:** 2025-06-26  
**基于文档:** @Doc/SPECIFICATIONS.md, @Doc/IMPLEMENTATION_PLAN.md, @html_data_cleansing.md

---

## 🚨 高风险模块与审查策略 (High-Risk Modules & Review Strategy)

### 关键风险识别 (Critical Risk Assessment)

基于对SEC 10-K文档复杂性和LLM处理要求的深入分析，识别出以下**AI可能难以高质量完成的高风险领域**：

#### 🔴 **高风险模块 1: 复杂财务表格解析**
**风险级别:** CRITICAL  
**影响范围:** TASK-003, TASK-008  
**风险描述:**
- SEC文档中的财务报表具有高度复杂的嵌套结构
- 多级表头、合并单元格、隐式层级关系
- 数值单位信息分散在表格内外
- 不同公司的表格格式存在显著差异

**具体挑战:**
```html
<!-- 示例: 复杂的多级表头结构 -->
<table>
  <tr>
    <th rowspan="2">Item</th>
    <th colspan="3">As of December 31</th>
  </tr>
  <tr>
    <th>2023</th>
    <th>2022</th>
    <th>2021</th>
  </tr>
  <tr>
    <td colspan="4">(in millions, except per share data)</td>
  </tr>
</table>
```

**缓解策略:**
1. **多层解析策略:** 实现pandas、BeautifulSoup、正则表达式的三层回退机制
2. **表格类型识别:** 建立财务报表类型的模式识别库
3. **严格测试要求:** 对表格处理模块要求95%+的测试覆盖率
4. **人工审查点:** 表格解析结果必须经过质量验证模块检查
5. **配置驱动:** 提供表格解析规则的外部配置文件

---

#### 🟠 **高风险模块 2: SEC文档结构识别**
**风险级别:** HIGH  
**影响范围:** TASK-004  
**风险描述:**
- 不同公司的10-K文档在格式上存在微妙但关键的差异
- ITEM和PART标题的标记方式不统一
- 嵌套的子章节结构复杂
- 某些公司使用非标准的章节命名

**具体挑战:**
```
公司A: "ITEM 1. BUSINESS"
公司B: "Item 1.    Business"  
公司C: "ITEM 1 - BUSINESS"
公司D: "PART I, ITEM 1. BUSINESS"
```

**缓解策略:**
1. **多模式匹配:** 实现至少5种不同的标题识别模式
2. **样本驱动开发:** 收集至少10家不同公司的10-K文档进行测试
3. **降级策略:** 结构识别失败时自动切换到固定长度分块
4. **模式学习:** 记录成功解析的模式，建立知识库
5. **手动干预接口:** 提供手动分块规则配置功能

---

#### 🟡 **高风险模块 3: 大文件内存管理**
**风险级别:** MEDIUM  
**影响范围:** TASK-010  
**风险描述:**
- 某些10-K文档超过100MB
- BeautifulSoup解析大文档时内存消耗激增
- 并行处理时内存使用叠加
- 系统可能在处理过程中崩溃

**缓解策略:**
1. **流式处理:** 实现基于生成器的流式HTML解析
2. **内存监控:** 添加实时内存使用监控和警告
3. **分段处理:** 对超大文档实施分段加载策略
4. **资源限制:** 设置进程级内存使用上限
5. **优雅降级:** 内存不足时自动降低并行度

---

### 审查流程 (Review Process)

#### 代码审查要求
```yaml
高风险模块审查标准:
  - 代码覆盖率: ≥95%
  - 集成测试: 必须包含真实数据测试
  - 性能测试: 必须通过压力测试
  - 错误处理: 100%覆盖所有异常路径
  - 文档完整性: 每个函数必须有详细docstring
  - 日志记录: 关键步骤必须有DEBUG级别日志
```

#### 质量门禁 (Quality Gates)
1. **单元测试通过率:** 100%
2. **集成测试通过率:** 100%  
3. **静态代码分析:** 无Critical和High级别问题
4. **内存泄漏检测:** 无内存泄漏
5. **性能基准:** 满足所有性能要求

---

## 🏗️ 系统架构设计 (System Architecture)

### 整体架构原则

#### 1. 模块化设计 (Modular Design)
```
核心原则: 高内聚、低耦合
- 每个模块职责单一
- 模块间通过明确的接口通信
- 支持独立测试和部署
```

#### 2. 容错设计 (Fault-Tolerant Design)
```
容错策略: 
- 优雅降级而非完全失败
- 详细的错误日志和恢复机制
- 部分失败不影响整体处理
```

#### 3. 可扩展性 (Scalability)
```
扩展支持:
- 插件式的处理器架构
- 配置驱动的行为定制
- 并行处理能力
```

### 系统层次架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户接口层 (UI Layer)                 │
├─────────────────────┬───────────────────────────────────┤
│     CLI Interface   │        API Interface             │
└─────────────────────┴───────────────────────────────────┘
           │                           │
           └─────────────┬─────────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│                   业务逻辑层 (Business Layer)            │
├─────────────────────────────────────────────────────────┤
│               Pipeline Orchestrator                     │
│  ┌─────────────┬─────────────┬─────────────────────────┐ │
│  │HTML Cleaner │Table Proc.  │  Document Chunker      │ │
│  └─────────────┴─────────────┴─────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
           │                           │
┌─────────────────────────────────────────────────────────┐
│                   服务层 (Service Layer)                │
├─────────────────────────────────────────────────────────┤
│  Logger │ Validator │ Config Manager │ Quality Checker  │
└─────────────────────────────────────────────────────────┘
           │                           │
┌─────────────────────────────────────────────────────────┐
│                   数据访问层 (Data Layer)                │
├─────────────────────────────────────────────────────────┤
│   File I/O   │   JSON Export   │   Report Generation   │
└─────────────────────────────────────────────────────────┘
```

### 核心组件设计

#### 1. Pipeline Orchestrator (管道编排器)
**职责:** 协调各个处理模块的执行流程
```python
class ProcessingPipeline:
    """主处理管道，协调所有处理步骤"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger()
        self.cleaner = HTMLCleaner()
        self.table_processor = TableProcessor()
        self.chunker = DocumentChunker()
        self.validator = QualityValidator()
    
    async def process_document(self, input_path: str) -> ProcessingResult:
        """处理单个文档的主入口"""
        pass
```

#### 2. HTML Cleaner (HTML清洗器)
**职责:** 执行HTML清洗和预处理
```python
class HTMLCleaner:
    """HTML清洗模块，移除噪音和格式化内容"""
    
    def clean_html(self, html_content: str) -> CleanedHTML:
        """基础HTML清洗"""
        pass
    
    def remove_boilerplate(self, soup: BeautifulSoup) -> BeautifulSoup:
        """移除样板文本"""
        pass
    
    def normalize_text(self, text: str) -> str:
        """文本标准化"""
        pass
```

#### 3. Table Processor (表格处理器)
**职责:** 处理和结构化HTML表格
```python
class TableProcessor:
    """表格处理模块，支持多种解析策略"""
    
    def __init__(self):
        self.strategies = [
            PandasStrategy(),
            BeautifulSoupStrategy(), 
            RegexStrategy()
        ]
    
    def process_tables(self, soup: BeautifulSoup) -> List[ProcessedTable]:
        """处理文档中的所有表格"""
        pass
    
    def identify_financial_tables(self, tables: List[Tag]) -> List[FinancialTable]:
        """识别财务报表类型的表格"""
        pass
```

#### 4. Document Chunker (文档分块器)
**职责:** 实现智能文档分块
```python
class DocumentChunker:
    """文档分块模块，支持语义分块"""
    
    def semantic_chunk(self, html_content: str) -> List[DocumentChunk]:
        """基于SEC文档结构的语义分块"""
        pass
    
    def identify_sections(self, soup: BeautifulSoup) -> List[SectionHeader]:
        """识别文档章节结构"""
        pass
    
    def fixed_length_chunk(self, text: str, max_length: int) -> List[DocumentChunk]:
        """固定长度分块（降级策略）"""
        pass
```

---

## 🛠️ 技术选型 (Technology Stack)

### 核心依赖 (Core Dependencies)

#### HTML解析和处理
```python
# Primary HTML Parser
beautifulsoup4>=4.12.0  # 主要HTML解析器
lxml>=4.9.0             # 高性能XML/HTML解析后端

# 数据处理
pandas>=2.0.0           # 表格数据处理
numpy>=1.24.0           # 数值计算支持
```

#### 系统工具
```python
# 异步和并发
asyncio                 # 异步编程支持（标准库）
concurrent.futures      # 并行处理支持（标准库）

# 日志和配置
loguru>=0.7.0          # 增强的日志系统
pydantic>=2.0.0        # 数据验证和配置管理
python-dotenv>=1.0.0   # 环境变量管理
```

#### CLI和API
```python
# 命令行界面
click>=8.1.0           # CLI框架
rich>=13.0.0           # 富文本终端输出
tqdm>=4.65.0           # 进度条

# API框架 (可选)
fastapi>=0.104.0       # 现代API框架
uvicorn>=0.24.0        # ASGI服务器
```

#### 开发和测试工具
```python
# 测试框架
pytest>=7.4.0         # 测试框架
pytest-asyncio>=0.21.0 # 异步测试支持
pytest-cov>=4.1.0     # 测试覆盖率

# 代码质量
black>=23.0.0          # 代码格式化
flake8>=6.0.0          # 代码检查
mypy>=1.5.0            # 类型检查
```

### 技术决策理由

#### 1. BeautifulSoup4 + lxml
**选择理由:**
- BeautifulSoup4: 提供直观的HTML操作API
- lxml: 高性能的C语言实现，处理大文件效率高
- 组合使用兼顾易用性和性能

#### 2. Pydantic用于配置管理
**选择理由:**
- 强类型的配置验证
- 自动生成配置文档
- 与IDE集成良好，提供代码提示

#### 3. Click用于CLI
**选择理由:**
- 装饰器风格的API设计简洁
- 内置帮助系统和参数验证
- 易于测试和维护

---

## 📁 目录结构设计 (Directory Structure)

```
edgar_cleaner/
├── pyproject.toml              # 项目配置和依赖
├── README.md                   # 项目说明文档
├── .env.example                # 环境变量示例
├── .gitignore                  # Git忽略规则
├── 
├── Doc/                        # 项目文档
│   ├── SPECIFICATIONS.md       # 需求规格
│   ├── IMPLEMENTATION_PLAN.md  # 实施计划
│   ├── DESIGN_AND_STANDARDS.md # 设计标准
│   └── API_DOCUMENTATION.md    # API文档
│
├── src/                        # 源代码目录
│   └── edgar_cleaner/          # 主包
│       ├── __init__.py
│       ├── main.py             # 程序入口
│       ├── config.py           # 配置管理
│       │
│       ├── core/               # 核心业务逻辑
│       │   ├── __init__.py
│       │   ├── pipeline.py     # 处理管道
│       │   ├── html_cleaner.py # HTML清洗
│       │   ├── table_processor.py # 表格处理
│       │   └── document_chunker.py # 文档分块
│       │
│       ├── models/             # 数据模型
│       │   ├── __init__.py
│       │   ├── document.py     # 文档模型
│       │   ├── table.py        # 表格模型
│       │   └── chunk.py        # 分块模型
│       │
│       ├── utils/              # 工具模块
│       │   ├── __init__.py
│       │   ├── logger.py       # 日志工具
│       │   ├── validators.py   # 数据验证
│       │   ├── file_utils.py   # 文件操作
│       │   └── text_utils.py   # 文本处理工具
│       │
│       ├── cli/                # 命令行接口
│       │   ├── __init__.py
│       │   ├── commands.py     # CLI命令
│       │   └── options.py      # CLI选项
│       │
│       └── api/                # API接口 (可选)
│           ├── __init__.py
│           ├── app.py          # FastAPI应用
│           ├── routes.py       # API路由
│           └── schemas.py      # API数据模式
│
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── conftest.py             # 测试配置
│   ├── test_data/              # 测试数据
│   │   ├── sample_10k.html     # 示例10-K文件
│   │   └── expected_output.json # 期望输出
│   │
│   ├── unit/                   # 单元测试
│   │   ├── test_html_cleaner.py
│   │   ├── test_table_processor.py
│   │   └── test_document_chunker.py
│   │
│   ├── integration/            # 集成测试
│   │   ├── test_pipeline.py
│   │   └── test_cli.py
│   │
│   └── performance/            # 性能测试
│       ├── test_memory_usage.py
│       └── test_processing_speed.py
│
├── config/                     # 配置文件
│   ├── default.yaml            # 默认配置
│   ├── development.yaml        # 开发环境配置
│   └── production.yaml         # 生产环境配置
│
├── scripts/                    # 脚本工具
│   ├── setup_dev_env.sh        # 开发环境设置
│   ├── run_tests.sh            # 测试运行脚本
│   └── benchmark.py            # 性能基准测试
│
└── output/                     # 输出目录
    ├── processed/              # 处理后的文档
    ├── logs/                   # 日志文件
    └── reports/                # 质量报告
```

---

## 📋 数据模型设计 (Data Models)

### 核心数据结构

#### 1. Document Model
```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentMetadata(BaseModel):
    """文档元数据"""
    file_path: str
    file_size: int
    company_name: Optional[str] = None
    cik: Optional[str] = None
    filing_date: Optional[datetime] = None
    form_type: str = "10-K"
    processing_timestamp: datetime
    
class ProcessedDocument(BaseModel):
    """处理后的文档"""
    metadata: DocumentMetadata
    chunks: List['DocumentChunk']
    tables: List['ProcessedTable']
    processing_stats: 'ProcessingStats'
    quality_metrics: Dict[str, Any]
```

#### 2. Chunk Model
```python
class DocumentChunk(BaseModel):
    """文档分块"""
    chunk_id: str
    section_title: str
    content: str
    char_count: int
    paragraph_count: int
    chunk_type: str  # "section", "paragraph", "table"
    source_location: Dict[str, int]  # 原始位置信息
    
class ChunkMetadata(BaseModel):
    """分块元数据"""
    extraction_method: str  # "semantic", "fixed_length"
    confidence_score: float
    contains_tables: bool
    contains_financial_data: bool
```

#### 3. Table Model  
```python
class TableCell(BaseModel):
    """表格单元格"""
    row: int
    col: int
    value: str
    colspan: int = 1
    rowspan: int = 1
    is_header: bool = False
    
class ProcessedTable(BaseModel):
    """处理后的表格"""
    table_id: str
    title: Optional[str] = None
    table_type: str  # "financial", "data", "summary"
    rows: int
    cols: int
    cells: List[TableCell]
    json_representation: Dict[str, Any]
    extraction_method: str
    confidence_score: float
```

---

## 🔧 开发标准 (Development Standards)

### 代码风格标准

#### 1. Python代码风格
```python
# 遵循PEP 8标准，使用black进行格式化

# 函数定义示例
def process_html_document(
    input_path: str,
    output_format: str = "json",
    config: Optional[Config] = None
) -> ProcessingResult:
    """
    处理HTML文档并返回结构化结果。
    
    Args:
        input_path: 输入HTML文件路径
        output_format: 输出格式 ("json", "markdown", "text")
        config: 可选的配置对象
        
    Returns:
        ProcessingResult: 包含处理结果和元数据
        
    Raises:
        FileNotFoundError: 输入文件不存在
        ProcessingError: 文档处理失败
        
    Example:
        >>> result = process_html_document("report.html", "json")
        >>> print(f"Processed {len(result.chunks)} chunks")
    """
    pass
```

#### 2. 类型提示要求
```python
# 所有公共函数必须包含完整的类型提示
from typing import List, Dict, Optional, Union, Protocol

class TableProcessor(Protocol):
    """表格处理器协议"""
    
    def process_table(self, table_html: str) -> ProcessedTable:
        """处理单个表格"""
        ...
    
    def batch_process(self, tables: List[str]) -> List[ProcessedTable]:
        """批量处理表格"""
        ...
```

#### 3. 错误处理标准
```python
# 自定义异常类
class EdgarCleanerError(Exception):
    """基础异常类"""
    pass

class HTMLParsingError(EdgarCleanerError):
    """HTML解析错误"""
    pass

class TableProcessingError(EdgarCleanerError):
    """表格处理错误"""
    pass

# 错误处理示例
def parse_financial_table(table_html: str) -> ProcessedTable:
    """解析财务表格"""
    try:
        # 尝试pandas解析
        return pandas_parse_table(table_html)
    except PandasError as e:
        logger.warning(f"Pandas parsing failed: {e}")
        try:
            # 回退到BeautifulSoup解析
            return beautifulsoup_parse_table(table_html)
        except Exception as e:
            logger.error(f"All table parsing methods failed: {e}")
            raise TableProcessingError(f"Unable to parse table: {e}")
```

### 测试标准

#### 1. 单元测试要求
```python
import pytest
from unittest.mock import patch, MagicMock

class TestHTMLCleaner:
    """HTML清洗器测试类"""
    
    def test_remove_scripts_and_styles(self):
        """测试脚本和样式移除功能"""
        html = """
        <html>
            <head><style>body{color:red}</style></head>
            <body>
                <script>alert('test')</script>
                <p>Content</p>
            </body>
        </html>
        """
        cleaner = HTMLCleaner()
        result = cleaner.clean_html(html)
        
        assert "<script>" not in result.cleaned_html
        assert "<style>" not in result.cleaned_html
        assert "Content" in result.cleaned_html
    
    @pytest.mark.parametrize("input_html,expected", [
        ("<br>", "\n"),
        ("<br/>", "\n"),
        ("<br />", "\n"),
    ])
    def test_br_tag_conversion(self, input_html, expected):
        """测试BR标签转换"""
        cleaner = HTMLCleaner()
        result = cleaner.normalize_text(input_html)
        assert expected in result
```

#### 2. 集成测试要求
```python
class TestProcessingPipeline:
    """处理管道集成测试"""
    
    @pytest.fixture
    def sample_10k_file(self):
        """提供示例10-K文件"""
        return "tests/test_data/sample_10k.html"
    
    def test_end_to_end_processing(self, sample_10k_file):
        """端到端处理测试"""
        pipeline = ProcessingPipeline()
        result = pipeline.process_document(sample_10k_file)
        
        # 验证基本输出结构
        assert result.metadata.file_path == sample_10k_file
        assert len(result.chunks) > 0
        assert len(result.tables) >= 0
        
        # 验证数据质量
        assert result.quality_metrics["processing_success"] is True
        assert result.quality_metrics["chunk_count"] > 0
```

### 性能标准

#### 1. 性能基准
```python
# 性能测试示例
import time
import psutil
import pytest

class TestPerformance:
    """性能测试"""
    
    def test_memory_usage_limit(self):
        """测试内存使用限制"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 处理大文件
        pipeline = ProcessingPipeline()
        pipeline.process_large_document("large_10k.html")
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长不应超过1GB
        assert memory_increase < 1024 * 1024 * 1024
    
    def test_processing_speed(self):
        """测试处理速度"""
        start_time = time.time()
        
        pipeline = ProcessingPipeline()
        result = pipeline.process_document("sample_5mb.html")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 5MB文件处理时间应少于30秒
        assert processing_time < 30
```

---

## 📊 配置管理 (Configuration Management)

### 配置架构

#### 1. 层次化配置
```yaml
# config/default.yaml
app:
  name: "EDGAR Cleaner"
  version: "1.0.0"
  
processing:
  chunk_size: 4000
  parallel_workers: 3
  enable_table_processing: true
  enable_quality_validation: true
  
html_cleaning:
  remove_scripts: true
  remove_styles: true
  remove_attributes: true
  normalize_whitespace: true
  
table_processing:
  strategies: ["pandas", "beautifulsoup", "regex"]
  financial_table_detection: true
  max_table_size: 10000
  
logging:
  level: "INFO"
  file: "logs/edgar_cleaner.log"
  max_size: "10MB"
  backup_count: 5
```

#### 2. 环境特定配置
```yaml
# config/development.yaml
logging:
  level: "DEBUG"
  console_output: true
  
processing:
  parallel_workers: 1  # 开发时使用单线程便于调试
  
# config/production.yaml  
processing:
  parallel_workers: 10
  enable_performance_monitoring: true
  
security:
  input_file_size_limit: "500MB"
  processing_timeout: 300
```

### 配置模型
```python
from pydantic import BaseSettings, Field
from typing import List

class ProcessingConfig(BaseModel):
    chunk_size: int = Field(default=4000, ge=1000, le=8000)
    parallel_workers: int = Field(default=3, ge=1, le=20)
    enable_table_processing: bool = True
    enable_quality_validation: bool = True

class HTMLCleaningConfig(BaseModel):
    remove_scripts: bool = True
    remove_styles: bool = True
    remove_attributes: bool = True
    normalize_whitespace: bool = True

class AppConfig(BaseSettings):
    """应用程序配置"""
    processing: ProcessingConfig = ProcessingConfig()
    html_cleaning: HTMLCleaningConfig = HTMLCleaningConfig()
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
```

---

## 🔍 质量保证体系 (Quality Assurance)

### 持续集成流程

#### 1. 代码质量检查
```bash
# scripts/quality_check.sh
#!/bin/bash

# 代码格式化检查
black --check src/ tests/

# 代码风格检查  
flake8 src/ tests/

# 类型检查
mypy src/

# 安全检查
bandit -r src/

# 依赖漏洞检查
safety check
```

#### 2. 测试流程
```bash
# scripts/run_tests.sh
#!/bin/bash

# 单元测试
pytest tests/unit/ -v --cov=src/edgar_cleaner --cov-report=html

# 集成测试
pytest tests/integration/ -v

# 性能测试
pytest tests/performance/ -v --benchmark-only
```

### 代码审查清单

#### 高风险模块专项检查
- [ ] **表格处理模块**
  - [ ] 是否实现了多种解析策略？
  - [ ] 是否有完整的错误处理和回退机制？
  - [ ] 是否测试了至少5种不同的表格格式？
  - [ ] 是否有性能基准测试？

- [ ] **文档分块模块**  
  - [ ] 是否支持多种标题识别模式？
  - [ ] 是否有降级策略（固定长度分块）？
  - [ ] 是否测试了不同公司的10-K格式？

- [ ] **内存管理**
  - [ ] 是否有内存使用监控？
  - [ ] 是否实现了流式处理？
  - [ ] 是否有内存泄漏测试？

---

**文档版本:** 1.0.0  
**最后更新:** 2025-06-26  
**下一阶段:** 核心开发执行 