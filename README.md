# 13F Institutional Holdings Tracker

## 项目简介 (Project Overview)

一个完整的SEC 13F机构持仓追踪系统，包含Django后端和React前端，用于爬取、存储、分析和展示机构投资者的13F-HR申报文件。

A complete SEC 13F institutional holdings tracking system with Django backend and React frontend for crawling, storing, analyzing, and displaying 13F-HR filings from institutional investors.

## 🎯 核心功能 (Core Features)

- ✅ **自动爬取** SEC 13F-HR申报文件
- ✅ **智能分析** 持仓变动（新建仓、加仓、减仓、清仓）
- ✅ **期权支持** Put/Call期权识别和分析
- ✅ **实时监控** 多个机构投资者
- ✅ **数据可视化** 仪表盘展示关键指标
- ✅ **定时更新** 每日/每周自动更新
- ✅ **RESTful API** 完整的后端接口

## 📁 项目结构 (Project Structure)

```
13f_web_new/
├── backend/                 # Django后端
│   ├── project_config/      # 项目配置
│   ├── crawler/             # 爬虫应用
│   ├── api/                 # REST API
│   ├── manage.py
│   ├── requirements.txt
│   └── README_CN.md
├── frontend/                # React前端
│   ├── src/
│   ├── public/
│   └── package.json
├── docs/                    # 文档
│   └── 集成开发文档.md
└── PROJECT_SUMMARY.md       # 项目总结
```

## 🚀 快速开始 (Quick Start)

### 后端启动 (Backend Setup)

```bash
cd backend

# 1. 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python manage.py migrate

# 4. 启动服务器
python manage.py runserver

# 访问: http://localhost:8000/api/
```

### 前端启动 (Frontend Setup)

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 配置环境变量
# 创建 .env 文件，添加:
# VITE_API_URL=http://localhost:8000/api

# 3. 启动开发服务器
npm run dev

# 访问: http://localhost:5173/
```

## 📊 技术栈 (Tech Stack)

### 后端 (Backend)
- **Python 3.11**
- **Django 5.0+** - Web框架
- **Django REST Framework** - API框架
- **SQLite3** - 数据库
- **Celery + Redis** - 异步任务
- **Pandas, BeautifulSoup** - 数据处理

### 前端 (Frontend)
- **React 18** - UI框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **TailwindCSS** - 样式框架
- **React Query** - 数据获取

## 🗄️ 数据库模型 (Database Models)

1. **Institution** (机构)
   - CIK编号、名称、资产管理规模

2. **Filing** (申报文件)
   - 报告期、提交日期、季度

3. **Holding** (持仓明细)
   - 股票代码、持股数量、市值
   - 变动信息（share_change, pct_change, action_type）

4. **OptionPosition** (期权持仓)
   - 期权类型（Call/Put）
   - 合约数量、名义价值

5. **CrawlLog** (爬虫日志)
   - 执行状态、处理文件数

## 🔌 API端点 (API Endpoints)

### Dashboard
- `GET /api/dashboard/summary` - 仪表盘摘要

### Institutions
- `GET /api/institutions/` - 机构列表
- `GET /api/institutions/{id}/` - 机构详情
- `POST /api/institutions/{id}/trigger_crawl/` - 触发爬取

### Filings
- `GET /api/filings/` - 申报文件列表
- `GET /api/filings/{id}/` - 文件详情

### Admin
- `GET /api/admin/companies` - 监控公司
- `POST /api/admin/companies/add` - 添加公司
- `GET /api/admin/system-status` - 系统状态

### Crawler
- `POST /api/crawler/trigger` - 手动触发
- `GET /api/crawler/status/{task_id}` - 任务状态

## 📝 开发文档 (Documentation)

- [项目总结](./PROJECT_SUMMARY.md) - 完整的开发总结
- [后端文档](./backend/README_CN.md) - 后端使用指南
- [集成文档](./docs/集成开发文档.md) - 技术规范

## ✅ 测试结果 (Test Results)

所有API端点测试通过：
```
✅ Dashboard Summary - 200 OK
✅ Institutions List - 200 OK
✅ Filings List - 200 OK
✅ Admin Companies - 200 OK
✅ System Status - 200 OK
✅ Add Institution - 201 Created
```

## 🎨 核心特性 (Key Features)

### 1. 智能差异计算
自动识别持仓变动类型：
- NEW - 新建仓
- Buy - 加仓
- Sell - 减仓
- Sold Out - 清仓
- Hold - 持有不变

### 2. 期权数据支持
- 自动识别Put/Call期权
- 分离存储期权持仓
- 计算期权名义价值

### 3. 异步任务调度
- 每日凌晨2点自动更新
- 每周五下午5点自动更新
- 支持手动触发更新
- 实时任务状态查询

### 4. 完整的管理后台
- Django Admin后台
- 机构管理
- 数据查看和编辑
- 日志监控

## 🛠️ 开发工具 (Development Tools)

### 后端测试
```bash
cd backend
python test_api.py
```

### 代码格式化
```bash
black .
isort .
flake8 .
```

### 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

## 📦 部署 (Deployment)

### 后端部署
1. 配置环境变量（DEBUG=False）
2. 收集静态文件：`python manage.py collectstatic`
3. 使用Gunicorn：`gunicorn project_config.wsgi:application`
4. 配置Nginx反向代理
5. 使用Supervisor管理Celery

### 前端部署
1. 构建生产版本：`npm run build`
2. 部署dist目录到静态服务器

## 🤝 贡献 (Contributing)

欢迎提交Issue和Pull Request！

## 📄 许可证 (License)

MIT License

## 📧 联系方式 (Contact)

如有问题，请查看文档或提交Issue。

---

**开发状态**: ✅ 后端核心功能已完成 | ⏳ 前端集成进行中

**最后更新**: 2026-02-02
