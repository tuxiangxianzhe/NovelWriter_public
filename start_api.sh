#!/bin/bash
# start_api.sh — 启动 NovelWriter FastAPI 后端
# 用法：bash start_api.sh [--dev]

cd "$(dirname "$0")"

if [ "$1" = "--dev" ]; then
    echo "=== 开发模式：后端 + 前端并行启动 ==="
    uvicorn api_server:app --host 0.0.0.0 --port 7860 --reload &
    BACKEND_PID=$!
    echo "后端 PID: $BACKEND_PID (http://localhost:7860)"
    cd frontend && npm run dev &
    FRONTEND_PID=$!
    echo "前端 PID: $FRONTEND_PID (http://localhost:3000)"
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT INT TERM
    wait
else
    echo "=== 生产模式：构建前端 + 启动后端 ==="
    if [ ! -d "frontend/dist" ]; then
        echo "构建前端..."
        cd frontend && npm install && npm run build && cd ..
    fi
    uvicorn api_server:app --host 0.0.0.0 --port 7860
fi
