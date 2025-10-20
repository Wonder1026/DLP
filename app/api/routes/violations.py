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