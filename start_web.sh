#!/bin/bash
# 启动 AI 小说生成器 Web 服务

echo "================================================"
echo "  AI 小说生成器 - Web 服务启动脚本"
echo "================================================"
echo ""

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到 python,请先安装 Python"
    exit 1
fi

echo "✅ Python 版本:"
python --version
echo ""

# 检查依赖
echo "📦 检查依赖..."
if ! python -c "import gradio" 2>/dev/null; then
    echo "⚠️  未安装 gradio,正在安装依赖..."
    pip install -r requirements.txt
fi

echo ""
echo "🚀 启动 Web 服务器..."
echo "   访问地址:"
echo "   - 本地: http://localhost:7860"
echo "   - 局域网: http://$(hostname -I | awk '{print $1}'):7860"
echo ""
echo "   按 Ctrl+C 停止服务"
echo "================================================"
echo ""

python web_server.py
