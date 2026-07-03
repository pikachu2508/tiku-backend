"""
题目路由：列表/单题/统计。

支持题型筛选、随机顺序、分页；可带 device_id，把该用户的进度状态 join 进来。
"""
import json
import random
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question, Progress
from ..schemas import QuestionOut

router = APIRouter(prefix="/questions", tags=["questions"])

TYPE_MAP = {"single": "single", "multi": "multi", "judge": "judge"}


def _attach_options(q: Question):
    """把 options/answer_norm 的 JSON 字符串安全解析成 list。"""
    opts = []
    if q.options:
        try:
            opts = json.loads(q.options)
        except Exception:
            opts = []
    norm = []
    if q.answer_norm:
        try:
            norm = json.loads(q.answer_norm)
        except Exception:
            norm = []
    return opts, norm


def _to_out(q: Question, status: Optional[str] = None, hide_answer: bool = True) -> dict:
    opts, norm = _attach_options(q)
    return {
        "id": q.id,
        "qid": q.qid,
        "type": q.type,
        "stem": q.stem,
        "options": opts,
        # 列表接口默认不返回答案，避免前端「偷看」；提交答题后由 progress 接口告知对错
        "answer": None if hide_answer else q.answer,
        "answer_norm": norm if not hide_answer else [],
        "category": q.category,
        "explanation": q.explanation,
        "status": status,
    }


# 前端老格式（v4.2 HTML）用的字段名映射：
#   type: single/multiple/truefalse    （后端是 single/multi/judge）
#   question: 题干                      （后端是 stem）
#   answer: single→'A', multiple→'ABCD', truefalse→true/false
TYPE_TO_LEGACY = {"single": "single", "multi": "multiple", "judge": "truefalse"}


def _to_legacy(q: Question, status: Optional[str] = None) -> dict:
    """按前端 v4.2 期望的格式输出（含答案——前端本地判题需要，不经过 hide_answer）。"""
    opts, norm = _attach_options(q)
    # 还原前端老格式的 answer
    if q.type == "judge":
        # norm = [True]/[False]
        answer = True if norm == [True] else (False if norm == [False] else None)
    elif q.type == "single":
        # norm = [0] -> "A"
        answer = "ABCDEFGH"[norm[0]] if norm and norm[0] in range(8) else (q.answer or "")
    else:  # multi
        answer = "".join("ABCDEFGH"[i] for i in norm if i in range(8)) or (q.answer or "")
    return {
        "id": q.id,
        "qid": q.qid or f"Q{q.id}",
        "type": TYPE_TO_LEGACY.get(q.type, q.type),
        "category": q.category or "招标代理",
        "question": q.stem,
        "options": opts,
        "answer": answer,
        "explanation": q.explanation,
        "status": status,
    }


@router.get("")
def list_questions(
    types: Optional[str] = Query(None, description="逗号分隔：single,multi,judge"),
    shuffle: bool = Query(False, description="随机顺序"),
    only_new: bool = Query(False, description="只看未做"),
    wrong_only: bool = Query(False, description="只看错题"),
    device_id: Optional[str] = Query(None, description="带上才能用 only_new/wrong_only 及返回 status"),
    fmt: str = Query("default", description="legacy=按前端 v4.2 字段名输出"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Question)
    if types:
        wanted = [t.strip() for t in types.split(",") if t.strip() in TYPE_MAP]
        if wanted:
            q = q.filter(Question.type.in_(wanted))

    # 该用户已做题的 id → status 映射
    status_map = {}
    if device_id:
        from ..models import User
        user = db.query(User).filter(User.device_id == device_id).first()
        if user:
            rows = (
                db.query(Progress)
                .filter(Progress.user_id == user.id)
                .all()
            )
            status_map = {r.question_id: r.status for r in rows}

            if only_new:
                done_ids = set(status_map.keys())
                q = q.filter(~Question.id.in_(done_ids)) if done_ids else q
            if wrong_only:
                wrong_ids = [qid for qid, st in status_map.items() if st == "wrong"]
                q = q.filter(Question.id.in_(wrong_ids)) if wrong_ids else q.filter(False)

    serialize = (lambda r, s=None: _to_legacy(r, s)) if fmt == "legacy" else _to_out

    total = q.count()
    if shuffle:
        # SQLite 没有 RANDOM() 便携写法，取全部 id 再打乱后取分页（题量 2308 可接受）
        all_ids = [r[0] for r in q.with_entities(Question.id).all()]
        random.shuffle(all_ids)
        page_ids = all_ids[offset: offset + limit]
        if not page_ids:
            items = []
        else:
            rows = db.query(Question).filter(Question.id.in_(page_ids)).all()
            id2row = {r.id: r for r in rows}
            items = [serialize(id2row[i], status_map.get(i)) for i in page_ids if i in id2row]
    else:
        q = q.order_by(Question.id).offset(offset).limit(limit)
        rows = q.all()
        items = [serialize(r, status_map.get(r.id)) for r in rows]

    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.get("/all/legacy")
def all_legacy(device_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """一次性返回全部题目（前端 v4.2 老格式），首屏加载用���
    题量 2262，约 1MB JSON，传输一次后浏览器缓存。"""
    status_map = {}
    if device_id:
        from ..models import User
        user = db.query(User).filter(User.device_id == device_id).first()
        if user:
            rows = db.query(Progress).filter(Progress.user_id == user.id).all()
            status_map = {r.question_id: r.status for r in rows}
    rows = db.query(Question).order_by(Question.id).all()
    return {"total": len(rows), "items": [_to_legacy(r, status_map.get(r.id)) for r in rows]}


@router.get("/stats/overview")
def overview(db: Session = Depends(get_db)):
    """题库总览（首页统计用）。"""
    from collections import Counter
    rows = db.query(Question.type).all()
    c = Counter(r[0] for r in rows)
    return {"total": sum(c.values()), "by_type": dict(c)}


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if q is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    data = _to_out(q, hide_answer=False)
    return data
