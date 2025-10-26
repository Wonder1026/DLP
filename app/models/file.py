from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from datetime import datetime
from app.database import Base


class UploadedFile(Base):
    """Модель загруженного файла"""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    filename = Column(String, nullable=False)  # Оригинальное имя файла
    file_path = Column(String, nullable=False)  # Путь к файлу на сервере
    file_size = Column(BigInteger, nullable=False)  # Размер в байтах
    file_type = Column(String, nullable=False)  # Тип файла (exe, docx и т.д.)
    mime_type = Column(String, nullable=True)  # MIME тип
    status = Column(String, default="pending")  # pending, approved, rejected
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
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }