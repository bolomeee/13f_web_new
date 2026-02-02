# 13F机构持仓追踪系统 - 后端

## 项目简介

这是一个完整的SEC 13F机构持仓追踪系统的Django后端，用于爬取、存储和分析机构投资者的13F-HR申报文件。

## 核心功能

### ✅ 已实现功能

1. **数据库模型**
   - 机构管理（Institution）
   - 申报文件（Filing）
   - 持仓明细（Holding）- 包含差异计算
   - 期权持仓（OptionPosition）- 支持Put/Call
   - 爬虫日志（CrawlLog）

2. **REST API接口**
   - 仪表盘数据聚合
   - 机构详情查询
   - 持仓变动分析
   - 期权数据展示
   - 系统管理接口

3. **爬虫系统**
   - SEC 13F数据提取
   - Put/Call期权识别
   - 自动差异计算
   - 异步任务处理

4. **异步任务**
   - Celery + Redis
   - 定时自动更新（每日/每周）
   - 手动触发爬取
   - 任务状态查询

## 技术栈

- **Python**: 3.11
- **框架**: Django 5.0+, Django REST Framework
- **数据库**: SQLite3
- **异步**: Celery + Redis
- **数据处理**: Pandas, BeautifulSoup

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python3.11 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env，修改SEC_USER_AGENT为您的邮箱
```

### 3. 初始化数据库

```bash
# 运行数据库迁移
python manage.py migrate

# 创建管理员账号（可选）
python manage.py createsuperuser
```

### 4. 启动服务

```bash
# 方式1：使用启动脚本
./start.sh

# 方式2：手动启动
python manage.py runserver
```

访问：
- API文档: http://localhost:8000/api/
- 管理后台: http://localhost:8000/admin/

### 5. 启动Celery（可选）

```bash
# 新终端1：启动Worker
celery -A project_config worker -l info

# 新终端2：启动Beat（定时任务）
celery -A project_config beat -l info
```

## API端点

### 仪表盘
- `GET /api/dashboard/summary` - 获取仪表盘数据

### 机构管理
- `GET /api/institutions/` - 机构列表
- `GET /api/institutions/{id}/` - 机构详情
- `POST /api/institutions/` - 创建机构
- `POST /api/institutions/{id}/trigger_crawl/` - 触发爬取

### 申报文件
- `GET /api/filings/` - 文件列表
- `GET /api/filings/{id}/` - 文件详情

### 系统管理
- `GET /api/admin/companies` - 监控公司列表
- `POST /api/admin/companies/add` - 添加公司
- `DELETE /api/admin/companies/{id}` - 删除公司
- `GET /api/admin/system-status` - 系统状态

### 爬虫控制
- `POST /api/crawler/trigger` - 手动触发爬虫
- `GET /api/crawler/status/{task_id}` - 查询任务状态

## 测试

```bash
# 运行API测试
python test_api.py
```

## 项目结构

```
backend/
├── project_config/      # Django配置
│   ├── settings.py      # 主配置
│   ├── urls.py          # 路由
│   └── celery.py        # Celery配置
├── crawler/             # 爬虫应用
│   ├── models.py        # 数据模型
│   ├── services.py      # 业务逻辑
│   ├── tasks.py         # 异步任务
│   └── admin.py         # 管理后台
├── api/                 # API应用
│   ├── views.py         # API视图
│   ├── serializers.py   # 序列化器
│   └── urls.py          # API路由
├── manage.py            # Django管理脚本
├── requirements.txt     # 依赖列表
└── README_CN.md         # 本文档
```

## 核心特性

### 1. 差异计算引擎

自动计算持仓变动：
- 新建仓（NEW）
- 加仓（Buy）
- 减仓（Sell）
- 清仓（Sold Out）
- 持有（Hold）

### 2. 期权支持

完整支持Put/Call期权：
- 自动识别期权类型
- 分离存储期权数据
- 计算名义价值

### 3. 异步任务

- 定时自动更新（每日凌晨2点）
- 每周更新（周五下午5点）
- 手动触发更新
- 任务状态实时查询

## 常见问题

### Q: 如何添加新的监控机构？

A: 通过API添加：
```bash
curl -X POST http://localhost:8000/api/admin/companies/add \
  -H "Content-Type: application/json" \
  -d '{"cik": "0001067983"}'
```

或在Django Admin中添加。

### Q: 如何查看日志？

A: 日志文件位于 `logs/django.log`

### Q: 如何修改定时任务时间？

A: 编辑 `project_config/celery.py` 中的 `beat_schedule` 配置。

## 开发指南

### 代码规范

```bash
# 格式化代码
black .

# 排序导入
isort .

# 检查代码质量
flake8 .
```

### 运行测试

```bash
pytest
```

### 创建新的迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

## 部署

### 生产环境配置

1. 修改`.env`：
   ```
   DEBUG=False
   DJANGO_SECRET_KEY=<生成新的密钥>
   ALLOWED_HOSTS=your-domain.com
   ```

2. 收集静态文件：
   ```bash
   python manage.py collectstatic
   ```

3. 使用Gunicorn：
   ```bash
   gunicorn project_config.wsgi:application --bind 0.0.0.0:8000
   ```

4. 配置Nginx反向代理

5. 使用Supervisor管理Celery

## 技术支持

如有问题，请查看：
- 项目总结: `../PROJECT_SUMMARY.md`
- 集成文档: `../docs/集成开发文档.md`
- Django文档: https://docs.djangoproject.com/

## 许可证

MIT License
