#!/bin/bash
# 13F Tracker 启动脚本 (Startup Script)

echo "🚀 启动13F Tracker后端服务..."
echo "=================================="

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python3.11 -m venv .venv"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查依赖
echo "📦 检查依赖..."
pip list | grep Django > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

# 运行迁移
echo "🗄️  运行数据库迁移..."
python manage.py migrate

# 启动服务器
echo "✅ 启动Django开发服务器..."
echo "   访问: http://localhost:8000/api/"
echo "   Admin: http://localhost:8000/admin/"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=================================="

python manage.py runserver 0.0.0.0:8000
