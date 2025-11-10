from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.database import Base

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.database import Base


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_super_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    violation_count = Column(Integer, default=0)  # ← добавили счётчик нарушений
    last_violation_at = Column(DateTime, nullable=True)  # ← время последнего нарушения
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "avatar": self.avatar,
            "is_admin": self.is_admin,
            "is_super_admin": self.is_super_admin,
            "is_banned": self.is_banned,
            "violation_count": self.violation_count,
            "last_violation_at": self.last_violation_at.strftime(
                "%Y-%m-%d %H:%M:%S") if self.last_violation_at else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

