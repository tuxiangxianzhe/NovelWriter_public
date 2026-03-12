@echo off
chcp 65001 >nul
:: 启动 AI 小说生成器 Web 服务 (Windows)

echo ================================================
echo   AI 小说生成器 - Web 服务启动脚本
echo ================================================
echo.

:: 检查 Python 环境
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Python,请先安装 Python 3.9+
    pause
    exit /b 1
)

echo ✅ Python 版本:
python --version
echo.

:: 检查依赖
echo 📦 检查依赖...
python -c "import gradio" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  未安装 gradio,正在安装依赖...
    pip install -r requirements.txt
)

echo.
echo 🚀 启动 Web 服务器...
echo    访问地址:
echo    - 本地: http://localhost:7860
echo.
echo    按 Ctrl+C 停止服务
echo ================================================
echo.

python web_server.py
pause
