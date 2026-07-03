"""
用户路由：免登录的 device_id 体系。

前端首次打开时生成一个 device_id（localStorage 存），首次请求时自动建用户。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserOut

router = APIRouter(prefix="", tags=["users"])


@router.post("", response_model=UserOut)
def upsert_user(payload: UserCreate, db: Session = Depends(get_db)):
    # payload 由 Pydantic 自动从请求体解析
    """按 device_id 找用户；没有就建一个。"""
    user = db.query(User).filter(User.device_id == payload.device_id).first()
    if user is None:
        user = User(device_id=payload.device_id, nickname=payload.nickname)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif payload.nickname and user.nickname != payload.nickname:
        user.nickname = payload.nickname
        db.commit()
        db.refresh(user)
    return user


@router.get("/{device_id}", response_model=UserOut)
def get_user(device_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.device_id == device_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在，请先 POST /users")
    return user
