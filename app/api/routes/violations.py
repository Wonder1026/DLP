from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.violation import Violation

router = APIRouter()


@router.get("/")
async def get_violations(
        admin_id: int,
        is_reviewed: bool = None,
        db: AsyncSession = Depends(get_db)
):
    """Получить список нарушений (только для админов)"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    # Получаем нарушения
    query = select(Violation).order_by(Violation.created_at.desc())

    if is_reviewed is not None:
        query = query.where(Violation.is_reviewed == is_reviewed)

    result = await db.execute(query)
    violations = result.scalars().all()

    return {
        "violations": [v.to_dict() for v in violations],
        "count": len(violations)
    }


@router.post("/{violation_id}/review")
async def mark_as_reviewed(
        violation_id: int,
        admin_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Отметить нарушение как проверенное"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    # Находим нарушение
    result = await db.execute(select(Violation).where(Violation.id == violation_id))
    violation = result.scalar_one_or_none()

    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Нарушение не найдено"
        )

    violation.is_reviewed = True
    await db.commit()

    return {
        "status": "success",
        "message": "Нарушение отмечено как проверенное"
    }


@router.get("/statistics")
async def get_statistics(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Получить статистику DLP системы"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    from app.models.message import Message
    from sqlalchemy import func

    # Общее количество сообщений
    result = await db.execute(select(func.count(Message.id)))
    total_messages = result.scalar() or 0

    # Количество нарушений
    result = await db.execute(select(func.count(Violation.id)))
    total_violations = result.scalar() or 0

    # Количество нарушений с конфиденциальными данными
    result = await db.execute(
        select(Violation).where(
            Violation.found_keywords.like('%карт%') |
            Violation.found_keywords.like('%Email%') |
            Violation.found_keywords.like('%телефон%') |
            Violation.found_keywords.like('%паспорт%') |
            Violation.found_keywords.like('%ИНН%') |
            Violation.found_keywords.like('%СНИЛС%')
        )
    )
    sensitive_violations = result.scalars().all()
    sensitive_count = len(sensitive_violations)

    # Процент блокировок
    block_rate = 0
    if total_messages > 0:
        block_rate = round((total_violations / total_messages) * 100, 1)

    # Количество заблокированных пользователей
    from app.models.user import User as UserModel
    result = await db.execute(
        select(func.count(UserModel.id)).where(UserModel.is_banned == True)
    )
    banned_users = result.scalar() or 0

    return {
        "total_messages": total_messages,
        "total_violations": total_violations,
        "sensitive_data_violations": sensitive_count,
        "block_rate": block_rate,
        "banned_users": banned_users
    }
