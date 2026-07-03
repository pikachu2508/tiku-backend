"""
FastAPI 入口。

启动方式（在项目根目录 招标代理题库_后端版/ 下）：
    uvicorn backend.main:app --reload --port 8000

启动后：
- API 文档（Swagger UI）：http://localhost:8000/docs
- 前端页面：http://localhost:8000/             （由 StaticFiles 挂载 frontend/）
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import users, questions, progress, explanations

app = FastAPI(
    title="招标代理题库 API",
    description=(
        "把单文件 HTML 题库升级为带后端的产品。"
        "原项目见《入选得到 AI 学习圈 2025-2026 AI 年度报告》第 252-261 页报道。"
    ),
    version="0.5.0",
)

# 允许前端跨域（开发期前后端分离；线上同源后可收紧）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "招标代理题库 API"}


# 挂路由
app.include_router(users.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(explanations.router, prefix="/api")


# 挂载前端静态文件（frontend/index.html 等）
HERE = Path(__file__).resolve().parent            # backend/
PROJECT_ROOT = HERE.parent                          # 招标代理题库_后端版/
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
