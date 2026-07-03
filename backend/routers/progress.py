"""
进度路由：提交作答、查询错题本、全局进度概览。

这是「多端同步」的核心——所有作答记到后端，换设备只要带同一个 device_id 即可同步。
"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from ..database import get_db
from ..models import User, Question, Attempt, Progress
from ..schemas import ProgressSummary

router = APIRouter(prefix="/progress", tags=["progress"])


class SubmitBody(BaseModel):
    device_id: str
    question_id: int
    selected: List = []
    mode: str = "browse"


def _get_or_create_user(db: Session, device_id: str) -> User:
    user = db.query(User).filter(User.device_id == device_id).first()
    if user is None:
        user = User(device_id=device_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _judge(question: Question, selected: List) -> bool:
    """把用户 selected 和 question.answer_norm 比对。"""
    try:
        norm = json.loads(question.answer_norm) if question.answer_norm else []
    except Exception:
        norm = []
    # 判断题：[0]=对 [1]=错，norm 里存的是 [true]/[false]，统一成 0/1 比对
    def _norm_idx(x):
        if x is True:
            return 0
        if x is False:
            return 1
        return x
    norm_set = set(_norm_idx(x) for x in norm)
    sel_set = set(selected)
    return norm_set == sel_set


@router.post("/submit")
def submit_attempt(body: SubmitBody, db: Session = Depends(get_db)):
    """
    提交一次作答。
    - 写一条流水 Attempt
    - 更新该题的 Progress 汇总（new/right/wrong）
    返回本次是否正确 + 标准答案（提交后允许看答案）。
    """
    user = _get_or_create_user(db, body.device_id)
    question = db.query(Question).filter(Question.id == body.question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    is_correct = _judge(question, body.selected)

    attempt = Attempt(
        user_id=user.id,
        question_id=question.id,
        selected=json.dumps(body.selected),
        is_correct=is_correct,
        mode=body.mode,
    )
    db.add(attempt)

    prog = (
        db.query(Progress)
        .filter(Progress.user_id == user.id, Progress.question_id == question.id)
        .first()
    )
    if prog is None:
        prog = Progress(
            user_id=user.id,
            question_id=question.id,
            status=("right" if is_correct else "wrong"),
            attempts_count=1,
            last_answered_at=datetime.utcnow(),
        )
        db.add(prog)
    else:
        prog.status = "right" if is_correct else "wrong"
        prog.attempts_count = (prog.attempts_count or 0) + 1
        prog.last_answered_at = datetime.utcnow()

    db.commit()
    db.refresh(attempt)

    # 返回判定 + 标准答案 + 解析（若有），前端据此显示「✅ 正确 / ❌ 错误 + 正确答案」
    return {
        "attempt_id": attempt.id,
        "is_correct": is_correct,
        "answer": question.answer,
        "explanation": question.explanation,
        "mode": attempt.mode,
        "answered_at": attempt.answered_at.isoformat() if attempt.answered_at else None,
    }


@router.get("/summary", response_model=ProgressSummary)
def get_summary(device_id: str = Query(...), db: Session = Depends(get_db)):
    """全局进度概览。"""
    from collections import Counter
    user = db.query(User).filter(User.device_id == device_id).first()
    total = db.query(Question).count()
    if user is None:
        return ProgressSummary(total=total, attempted=0, right=0, wrong=0, new=total, accuracy=0.0)

    rows = db.query(Progress.status).filter(Progress.user_id == user.id).all()
    c = Counter(r[0] for r in rows)
    attempted = sum(c.values())
    right = c.get("right", 0)
    wrong = c.get("wrong", 0)
    acc = (right / attempted) if attempted else 0.0
    return ProgressSummary(
        total=total,
        attempted=attempted,
        right=right,
        wrong=wrong,
        new=max(total - attempted, 0),
        accuracy=round(acc, 4),
    )


@router.get("/wrong")
def get_wrong_questions(
    device_id: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """错题本：返回该用户做错过的题。"""
    user = db.query(User).filter(User.device_id == device_id).first()
    if user is None:
        return {"total": 0, "items": []}

    q = (
        db.query(Question, Progress)
        .join(Progress, Progress.question_id == Question.id)
        .filter(Progress.user_id == user.id, Progress.status == "wrong")
        .order_by(Progress.last_answered_at.desc())
    )
    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    items = []
    for question, prog in rows:
        try:
            opts = json.loads(question.options) if question.options else []
        except Exception:
            opts = []
        items.append({
            "id": question.id,
            "qid": question.qid,
            "type": question.type,
            "stem": question.stem,
            "options": opts,
            "answer": question.answer,
            "status": prog.status,
            "attempts_count": prog.attempts_count,
            "explanation": question.explanation,
        })
    return {"total": total, "limit": limit, "offset": offset, "items": items}
