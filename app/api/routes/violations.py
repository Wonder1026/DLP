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
    """Получить расширенную статистику DLP системы"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    from app.models.message import Message
    from app.models.file import UploadedFile
    from app.models.url_check import URLCheck
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Общее количество сообщений
    result = await db.execute(select(func.count(Message.id)))
    total_messages = result.scalar() or 0

    # Количество нарушений
    result = await db.execute(select(func.count(Violation.id)))
    total_violations = result.scalar() or 0

    # Нарушения за последние 7 дней (по дням)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(Violation).where(Violation.created_at >= seven_days_ago)
    )
    recent_violations = result.scalars().all()

    # Группируем по дням
    violations_by_day = {}
    for i in range(7):
        date = (datetime.utcnow() - timedelta(days=6 - i)).strftime('%d.%m')
        violations_by_day[date] = 0

    for violation in recent_violations:
        date_key = violation.created_at.strftime('%d.%m')
        if date_key in violations_by_day:
            violations_by_day[date_key] += 1

    # Количество нарушений с конфиденциальными данными
    sensitive_count = len([v for v in recent_violations if any(
        keyword in (v.found_keywords or '')
        for keyword in ['карт', 'Email', 'телефон', 'паспорт', 'ИНН', 'СНИЛС']
    )])

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

    # Статистика по файлам
    result = await db.execute(select(func.count(UploadedFile.id)))
    total_files = result.scalar() or 0

    result = await db.execute(
        select(func.count(UploadedFile.id)).where(UploadedFile.status == "pending")
    )
    pending_files = result.scalar() or 0

    result = await db.execute(
        select(func.count(UploadedFile.id)).where(UploadedFile.status == "approved")
    )
    approved_files = result.scalar() or 0

    result = await db.execute(
        select(func.count(UploadedFile.id)).where(UploadedFile.status == "rejected")
    )
    rejected_files = result.scalar() or 0

    # Статистика по URL
    result = await db.execute(select(func.count(URLCheck.id)))
    total_urls = result.scalar() or 0

    result = await db.execute(
        select(func.count(URLCheck.id)).where(URLCheck.status == "malicious")
    )
    malicious_urls = result.scalar() or 0

    result = await db.execute(
        select(func.count(URLCheck.id)).where(URLCheck.status == "safe")
    )
    safe_urls = result.scalar() or 0

    # Топ нарушителей
    result = await db.execute(
        select(UserModel)
        .where(UserModel.violation_count > 0)
        .order_by(UserModel.violation_count.desc())
        .limit(5)
    )
    top_violators = result.scalars().all()

    return {
        "total_messages": total_messages,
        "total_violations": total_violations,
        "sensitive_data_violations": sensitive_count,
        "block_rate": block_rate,
        "banned_users": banned_users,
        "violations_by_day": violations_by_day,
        "files": {
            "total": total_files,
            "pending": pending_files,
            "approved": approved_files,
            "rejected": rejected_files
        },
        "urls": {
            "total": total_urls,
            "malicious": malicious_urls,
            "safe": safe_urls
        },
        "top_violators": [
            {
                "username": u.username,
                "display_name": u.display_name,
                "violation_count": u.violation_count,
                "is_banned": u.is_banned
            }
            for u in top_violators
        ]
    }
