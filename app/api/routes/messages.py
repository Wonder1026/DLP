from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.message import Message

router = APIRouter()


@router.get("/")
async def get_messages(db: AsyncSession = Depends(get_db)):
    """Получить все сообщения из БД"""
    result = await db.execute(select(Message).order_by(Message.timestamp))
    messages = result.scalars().all()

    return {
        "messages": [msg.to_dict() for msg in messages]
    }


@router.get("/history")
async def get_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Получить последние N сообщений"""
    result = await db.execute(
        select(Message)
        .order_by(Message.timestamp.desc())
        .limit(limit)
    )
    messages = result.scalars().all()

    return {
        "messages": [msg.to_dict() for msg in reversed(messages)]
    }