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
    is_banned = Column(Boolean, default=False)  # Забанен или нет
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Преобразование в словарь (БЕЗ пароля!)"""
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "avatar": self.avatar,
            "is_admin": self.is_admin,
            "is_super_admin": self.is_super_admin,
            "is_banned": self.is_banned,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }