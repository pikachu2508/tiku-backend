"""
Pydantic 数据校验：API 入参/出参的形状。

这些类不是表结构，是「接口契约」——前端按这个格式发/收数据。
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- 题目 ----------
class QuestionOut(BaseModel):
    id: int
    qid: Optional[str] = None
    type: str
    stem: str
    options: List[str] = []
    answer: Optional[str] = None            # 原始答案（提交后才返回，避免偷看）
    answer_norm: List = []                  # 归一化答案
    category: Optional[str] = None
    explanation: Optional[str] = None
    # 该用户对此题的当前状态（join 进来）
    status: Optional[str] = None            # 'new' | 'right' | 'wrong'

    class Config:
        from_attributes = True


# ---------- 用户 ----------
class UserCreate(BaseModel):
    device_id: str
    nickname: Optional[str] = None


class UserOut(BaseModel):
    id: int
    device_id: str
    nickname: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- 答题 ----------
class SubmitAttempt(BaseModel):
    """前端提交一次作答。"""
    question_id: int
    selected: List = Field(..., description="用户选的索引，如 [0] 或 [0,2]；判断题 [0]=对 [1]=错")
    mode: str = "browse"


class AttemptOut(BaseModel):
    id: int
    question_id: int
    selected: List
    is_correct: bool
    mode: str
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- 进度 ----------
class ProgressSummary(BaseModel):
    """用户的全局进度概览（首页统计条用）。"""
    total: int
    attempted: int
    right: int
    wrong: int
    new: int
    accuracy: float       # 正确率 0~1


class ExplainRequest(BaseModel):
    """请求生成 AI 解析。"""
    question_id: int
