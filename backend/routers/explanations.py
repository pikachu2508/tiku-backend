"""
AI 解析路由（预留）。

背景：原始 Excel 题库只有答案没有解析——这是用户（报道里的朋友慕云）的核心痛点之一，
他复习时要翻书或截图问 DeepSeek。

本次迭代先把这个「接口位置」留出来：
- GET /explanations/{question_id}：若库里已有解析就返回；没有就返回占位。
- POST /explanations/{question_id}：触发「生成」——当前返回占位文本，
  下次接上真实大模型 API（DeepSeek / 智谱 / 通义千问）时，只改这个文件即可。

接 API 时的改造点（备忘）：
    import os, httpx
    API_KEY = os.getenv("LLM_API_KEY")
    resp = httpx.post("https://api.deepseek.com/v1/chat/completions",
                      headers={"Authorization": f"Bearer {API_KEY}"}, json={...})
    把返回的文本写入 question.explanation 并 commit。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question

router = APIRouter(prefix="/explanations", tags=["explanations"])

PLACEHOLDER_NOTE = (
    "【AI 解析功能预留】这条题目的解析还没生成。\n"
    "本次迭代已把数据库字段和接口位置预留好，后续接入大模型 API（DeepSeek / 智谱 / 通义千问）后，"
    "这里会自动填充：知识点定位、答案推理过程、易错点提示。\n"
    "——这正是把「单文件 HTML 题库」升级为「个性化备考私人教练」的关键一步。"
)


@router.get("/{question_id}")
def get_explanation(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if q is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    if q.explanation:
        return {"question_id": question_id, "explanation": q.explanation, "generated": True}
    return {"question_id": question_id, "explanation": PLACEHOLDER_NOTE, "generated": False}


@router.post("/{question_id}")
def generate_explanation(question_id: int, db: Session = Depends(get_db)):
    """触发「生成」。当前为占位实现——返回提示文本，不写库。"""
    q = db.query(Question).filter(Question.id == question_id).first()
    if q is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    # TODO（接 API 后）：调大模型生成解析，写入 q.explanation 后 commit。
    return {"question_id": question_id, "explanation": PLACEHOLDER_NOTE, "generated": False}
