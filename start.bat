@echo off
chcp 65001 >nul
title 招标代理题库 - 后端版
cd /d "%~dp0"

echo ============================================
echo   招标代理题库 - 后端版 启动
echo ============================================
echo.

REM 首次运行：检查并安装依赖
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [首次运行] 正在安装依赖...
    pip install -r requirements.txt
    echo.
)

REM 首次运行：题库未导入则自动导入
if not exist "backend\quiz.db" (
    echo [首次运行] 正在导入题库到数据库...
    python -m backend.import_xlsx
    echo.
)

echo 正在启动服务...
echo 启动后请访问: http://127.0.0.1:8000
echo 按 Ctrl+C 可停止服务
echo.

REM 3 秒后自动打开浏览器
start "" timeout /t 3 /nobreak >nul ^& start "" "http://127.0.0.1:8000"

python -m uvicorn backend.main:app --port 8000
pause
