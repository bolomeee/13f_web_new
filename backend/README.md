# 13F Tracker Backend

## 项目简介 (Project Overview)

这是一个基于Django 5.0的13F机构持仓追踪系统后端，用于爬取、存储和分析SEC 13F-HR申报文件。

This is a Django 5.0 based backend for 13F institutional holdings tracking system, designed to crawl, store, and analyze SEC 13F-HR filings.

## 技术栈 (Tech Stack)

- **Python**: 3.11+
- **Web Framework**: Django 5.0+
- **REST API**: Django REST Framework
- **Database**: SQLite3
- **Async Tasks**: Celery + Redis
- **Data Processing**: Pandas, BeautifulSoup, lxml

## 项目结构 (Project Structure)

```
backend/
├── project_config/      # Django项目配置
│   ├── settings.py      # 主配置文件
│   ├── urls.py          # 主URL路由
│   ├── celery.py        # Celery配置
│   └── wsgi.py          # WSGI入口
├── crawler/             # 爬虫应用
│   ├── models.py        # 数据库模型
│   ├── services.py      # 业务逻辑层
│   ├── tasks.py         # Celery异步任务
│   ├── admin.py         # Django Admin配置
│   ├── edgar_downloader.py  # SEC下载器
│   └── sec_13f_extractor.py # 13F数据提取器
├── api/                 # REST API应用
│   ├── views.py         # API视图
│   ├── serializers.py   # 序列化器
│   └── urls.py          # API路由
├── manage.py            # Django管理脚本
├── requirements.txt     # Python依赖
└── .env                 # 环境变量配置
```

## 快速开始 (Quick Start)

### 1. 安装依赖 (Install Dependencies)

```bash
# 创建虚拟环境 (Create virtual environment)
python3.11 -m venv .venv

# 激活虚拟环境 (Activate virtual environment)
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 安装依赖 (Install dependencies)
pip install -r requirements.txt
```

### 2. 配置环境变量 (Configure Environment Variables)

```bash
# 复制环境变量模板 (Copy environment template)
cp .env.example .env

# 编辑.env文件，修改必要的配置 (Edit .env file)
# 特别是SEC_USER_AGENT，需要填写您的联系邮箱
```

### 3. 初始化数据库 (Initialize Database)

```bash
# 创建数据库迁移 (Create database migrations)
python manage.py makemigrations

# 执行迁移 (Run migrations)
python manage.py migrate

# 创建超级用户（可选，用于访问Django Admin）
python manage.py createsuperuser
```

### 4. 启动开发服务器 (Start Development Server)

```bash
# 启动Django开发服务器 (Start Django dev server)
python manage.py runserver

# 访问 (Access):
# - API: http://localhost:8000/api/
# - Admin: http://localhost:8000/admin/
```

### 5. 启动Celery Worker（可选）(Start Celery Worker - Optional)

在新的终端窗口中：

```bash
# 确保Redis正在运行 (Make sure Redis is running)
redis-server

# 在另一个终端启动Celery Worker
celery -A project_config worker -l info

# 启动Celery Beat（定时任务调度器）
celery -A project_config beat -l info
```

## API端点 (API Endpoints)

### Dashboard (仪表盘)

- `GET /api/dashboard/summary` - 获取仪表盘摘要数据

### Institutions (机构)

- `GET /api/institutions/` - 获取机构列表
- `GET /api/institutions/{id}/` - 获取机构详情
- `POST /api/institutions/` - 创建机构
- `GET /api/institutions/{id}/latest_filing/` - 获取最新申报
- `POST /api/institutions/{id}/trigger_crawl/` - 触发爬取

### Filings (申报文件)

- `GET /api/filings/` - 获取申报文件列表
- `GET /api/filings/{id}/` - 获取申报文件详情

### Admin (管理)

- `GET /api/admin/companies` - 获取监控公司列表
- `POST /api/admin/companies/add` - 添加监控公司
- `DELETE /api/admin/companies/{id}` - 删除监控公司
- `GET /api/admin/system-status` - 获取系统状态

### Crawler (爬虫)

- `POST /api/crawler/trigger` - 手动触发爬虫
- `GET /api/crawler/status/{task_id}` - 查询任务状态

## 数据库模型 (Database Models)

### Institution (机构)
- CIK编号、机构名称、资产管理规模等

### Filing (申报文件)
- 报告期、提交日期、文件编号等

### Holding (持仓明细)
- 股票代码、持股数量、市值、变动信息等

### OptionPosition (期权持仓)
- 期权类型（Call/Put）、合约数量、名义价值等

### CrawlLog (爬虫日志)
- 执行状态、处理文件数、错误信息等

## 开发指南 (Development Guide)

### 运行测试 (Run Tests)

```bash
pytest
```

### 代码格式化 (Code Formatting)

```bash
# 使用black格式化代码
black .

# 使用isort排序导入
isort .

# 使用flake8检查代码质量
flake8 .
```

### 创建新的迁移 (Create New Migration)

```bash
python manage.py makemigrations
python manage.py migrate
```

### 访问Django Shell (Access Django Shell)

```bash
python manage.py shell
```

## 部署 (Deployment)

### 生产环境配置 (Production Configuration)

1. 修改`.env`文件：
   - 设置`DEBUG=False`
   - 生成新的`DJANGO_SECRET_KEY`
   - 配置`ALLOWED_HOSTS`

2. 收集静态文件：
   ```bash
   python manage.py collectstatic
   ```

3. 使用Gunicorn运行：
   ```bash
   gunicorn project_config.wsgi:application --bind 0.0.0.0:8000
   ```

4. 配置Nginx作为反向代理

5. 使用Supervisor管理Celery进程

## 常见问题 (FAQ)

### Q: 如何添加新的监控机构？

A: 通过API端点 `POST /api/admin/companies/add` 或在Django Admin中添加。

### Q: 爬虫多久运行一次？

A: 默认配置为每日凌晨2点和每周五下午5点自动运行。可在`project_config/celery.py`中修改。

### Q: 如何查看爬虫日志？

A: 查看`logs/django.log`文件或访问Django Admin的爬虫日志页面。

## 许可证 (License)

MIT License

## 联系方式 (Contact)

如有问题，请联系项目维护者。
