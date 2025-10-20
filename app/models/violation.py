from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from app.database import Base


class Violation(Base):
    """Модель нарушения DLP правил"""
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # ID нарушителя
    username = Column(String, nullable=False)  # Username нарушителя
    display_name = Column(String, nullable=False)  # Отображаемое имя
    message_text = Column(Text, nullable=False)  # Текст сообщения
    found_keywords = Column(String, nullable=True)  # Найденные ключевые слова (через запятую)
    violation_type = Column(String, default="keyword")  # Тип нарушения
    is_reviewed = Column(Boolean, default=False)  # Проверено администратором
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "message_text": self.message_text,
            "found_keywords": self.found_keywords.split(',') if self.found_keywords else [],
            "violation_type": self.violation_type,
            "is_reviewed": self.is_reviewed,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }