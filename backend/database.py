"""
SQLite 数据库连接与会话。

设计要点：
- 用 SQLite 单文件（quiz.db），零配置，本地直接跑。
- 后期迁 Cloudflare D1 / Turso 时，只需把 create_engine 的 URL 换成远程地址。
- check_same_thread=False：FastAPI 多线程下 SQLite 需要。
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = "quiz.db"
# 始终把数据库建在 backend/ 目录下（与代码一起）
BACKEND_DIR = Path(__file__).resolve().parent
SQLALCHEMY_DATABASE_URL = f"sqlite:///{BACKEND_DIR / DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖：每个请求拿一个独立 session，请求结束自动关。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表（已存在则跳过）。启动时调用一次。"""
    # 必须先 import models，Base.metadata 才知道有哪些表
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
