from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from app.database import Base


class URLCheck(Base):
    """Модель проверки URL"""
    __tablename__ = "url_checks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    message_text = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, safe, malicious, suspicious
    virustotal_result = Column(Text, nullable=True)
    is_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "url": self.url,
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "message_text": self.message_text,
            "status": self.status,
            "virustotal_result": self.virustotal_result,
            "is_reviewed": self.is_reviewed,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }