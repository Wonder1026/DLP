from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from app.models.violation import Violation
from datetime import datetime


class ViolationService:
    """Сервис для управления нарушениями"""

    VIOLATION_THRESHOLD = 10  # Порог для автобана

    async def register_violation(
            self,
            db: AsyncSession,
            user_id: int,
            message_text: str,
            found_items: list
    ) -> dict:
        """
        Регистрация нарушения

        Возвращает информацию о статусе пользователя
        """
        # Получаем пользователя
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {"error": "User not found"}

        # Увеличиваем счётчик нарушений
        user.violation_count += 1
        user.last_violation_at = datetime.utcnow()

        # Проверяем порог
        should_ban = user.violation_count >= self.VIOLATION_THRESHOLD and not user.is_admin

        if should_ban:
            user.is_banned = True

        await db.commit()
        await db.refresh(user)

        return {
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "violation_count": user.violation_count,
            "is_banned": user.is_banned,
            "should_notify_admin": should_ban or user.violation_count % 5 == 0
            # Уведомляем при бане или каждые 5 нарушений
        }

    async def reset_violations(self, db: AsyncSession, user_id: int):
        """Сброс счётчика нарушений"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(violation_count=0, last_violation_at=None)
        )
        await db.commit()


violation_service = ViolationService()