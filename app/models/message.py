from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class Message(Base):
    """Модель сообщения"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, nullable=False)
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "user": self.user,
            "text": self.text,
            "timestamp": self.timestamp.strftime("%H:%M:%S")
        }
