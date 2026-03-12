# api_server.py
# -*- coding: utf-8 -*-
"""
NovelWriter FastAPI 后端入口
替代 web_server.py（Gradio）

启动命令：
    uvicorn api_server:app --host 0.0.0.0 --port 7860 --reload
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

app = FastAPI(
    title="NovelWriter API",
    description="AI 小说生成器 REST + SSE API",
    version="2.0.0",
)

# CORS —— 开发阶段允许本地前端（:3000）访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 挂载路由 ─────────────────────────────────────────────────────────────────

from api.routers import (
    projects, config, presets, generate,
    styles, knowledge, files, logs, consistency,
)

app.include_router(projects.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(presets.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(styles.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(consistency.router, prefix="/api")

# ── 健康检查 ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# ── 生产模式：serve Vue 构建产物 ───────────────────────────────────────────────

_frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="static")
    logging.getLogger(__name__).info(f"Serving frontend from {_frontend_dist}")
else:
    logging.getLogger(__name__).info(
        "Frontend dist not found. Run 'cd frontend && npm run build' to build the UI."
    )
