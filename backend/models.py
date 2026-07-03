"""
SQLAlchemy 表结构定义（ORM）。

四张表的设计理由见项目 README「数据库 Schema」一节。
核心点：
- explanation 字段先留 NULL，为「AI 智能解析」铺路，下次接 API 时只动 routers/explanations.py。
- device_id 免登录设计，降低作品集体验门槛。
- attempts（流水）与 progress（汇总）分表：前者看历史轨迹，后者看错题本/未做题。
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    qid = Column(Text, index=True)              # 原序号，如 "单选-1"
    type = Column(Text, index=True)             # 'single' | 'multi' | 'judge'
    stem = Column(Text)                         # 题干
    options = Column(Text)                      # JSON 字符串：["项A","项B",...]
    answer = Column(Text)                       # 原始答案："A" / "ABCD" / "对"
    answer_norm = Column(Text)                  # 归一化 JSON：[0] / [0,1,2,3] / [true]
    category = Column(Text, nullable=True)      # 知识点分类，预留先空
    explanation = Column(Text, nullable=True)   # ★ AI 解析，预留先空
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship("Attempt", back_populates="question")
    progress_records = relationship("Progress", back_populates="question")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Text, unique=True, index=True)  # 浏览器生成，免登录
    nickname = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship("Attempt", back_populates="user")
    progress_records = relationship("Progress", back_populates="user")


class Attempt(Base):
    """答题流水：每次作答记一条。"""
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), index=True)
    selected = Column(Text)                     # 用户选的，JSON：[0,2]
    is_correct = Column(Boolean)
    mode = Column(Text)                         # 'browse' | 'exam' | 'flash'
    answered_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")


class Progress(Base):
    """题目级汇总：每题的最新状态，给「只看未做 / 错题本」用。"""
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question"),)

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), primary_key=True)
    status = Column(Text)                       # 'new' | 'right' | 'wrong'
    attempts_count = Column(Integer, default=0)
    last_answered_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="progress_records")
    question = relationship("Question", back_populates="progress_records")
