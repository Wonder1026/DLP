from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text
from datetime import datetime
from app.database import Base


class UploadedFile(Base):
    """Модель загруженного файла"""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    moderation_type = Column(String, default="manual")  # manual, virustotal
    virustotal_result = Column(Text, nullable=True)  # JSON результат от VirusTotal
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "status": self.status,
            "moderation_type": self.moderation_type,
            "virustotal_result": self.virustotal_result,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

