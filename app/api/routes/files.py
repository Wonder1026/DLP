from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
import uuid
from datetime import datetime
from app.database import get_db
from app.models.file import UploadedFile
from app.models.user import User
from app.websocket.manager import manager

router = APIRouter()

# Папка для загрузки файлов
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Разрешённые типы файлов
ALLOWED_EXTENSIONS = {".exe", ".doc", ".docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload")
async def upload_file(
        user_id: int,
        moderation_type: str = "manual",  # ← добавили параметр
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    """Загрузка файла"""

    # Проверяем пользователя
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Проверяем тип модерации
    if moderation_type not in ["manual", "virustotal"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимый тип модерации. Разрешены: manual, virustotal"
        )

    # Проверяем расширение файла
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Читаем файл
    content = await file.read()
    file_size = len(content)

    # Проверяем размер
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимум: {MAX_FILE_SIZE // 1024 // 1024} MB"
        )

    # Генерируем уникальное имя файла
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Сохраняем файл
    with open(file_path, "wb") as f:
        f.write(content)

    # Сохраняем информацию в БД
    uploaded_file = UploadedFile(
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=file_ext.replace(".", ""),
        mime_type=file.content_type,
        status="pending",
        moderation_type=moderation_type  # ← сохраняем тип модерации
    )

    db.add(uploaded_file)
    await db.commit()
    await db.refresh(uploaded_file)

    moderation_text = "ручную модерацию" if moderation_type == "manual" else "проверку VirusTotal"
    print(f"📎 Файл загружен: {file.filename} от {user.display_name} (тип модерации: {moderation_type})")

    return {
        "status": "success",
        "message": f"Файл загружен и отправлен на {moderation_text}",
        "file": uploaded_file.to_dict()
    }


@router.get("/list")
async def get_files(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить список файлов пользователя"""

    result = await db.execute(
        select(UploadedFile)
        .where(UploadedFile.user_id == user_id)
        .order_by(UploadedFile.created_at.desc())
    )
    files = result.scalars().all()

    return {
        "files": [f.to_dict() for f in files]
    }


@router.get("/pending")
async def get_pending_files(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Получить файлы на модерации (только для админов)"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    # Получаем файлы на модерации
    result = await db.execute(
        select(UploadedFile)
        .where(UploadedFile.status == "pending")
        .order_by(UploadedFile.created_at.desc())
    )
    files = result.scalars().all()

    return {
        "files": [f.to_dict() for f in files],
        "count": len(files)
    }


@router.get("/all")
async def get_all_files(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Получить все файлы (только для админов)"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    # Получаем все файлы
    result = await db.execute(
        select(UploadedFile).order_by(UploadedFile.created_at.desc())
    )
    files = result.scalars().all()

    return {
        "files": [f.to_dict() for f in files],
        "count": len(files)
    }


@router.post("/{file_id}/approve")
async def approve_file(
        file_id: int,
        admin_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Одобрить файл"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    # Находим файл
    result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
    file_obj = result.scalar_one_or_none()

    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден"
        )

    file_obj.status = "approved"
    await db.commit()
    await db.refresh(file_obj)

    print(f"✅ Файл одобрен: {file_obj.filename}")

    # 📢 Отправляем уведомление всем через WebSocket
    await manager.broadcast({
        "type": "file_status_update",
        "file_id": file_obj.id,
        "status": "approved"
    })

    return {
        "status": "success",
        "message": f"Файл '{file_obj.filename}' одобрен",
        "file": file_obj.to_dict()
    }


@router.get("/pending")
async def get_pending_files(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Получить файлы на модерации (только для админов)"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    # Получаем файлы на модерации
    result = await db.execute(
        select(UploadedFile)
        .where(UploadedFile.status == "pending")
        .order_by(UploadedFile.created_at.desc())
    )
    files = result.scalars().all()

    return {
        "files": [f.to_dict() for f in files],
        "count": len(files)
    }


@router.get("/all")
async def get_all_files(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Получить все файлы (только для админов)"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    # Получаем все файлы
    result = await db.execute(
        select(UploadedFile).order_by(UploadedFile.created_at.desc())
    )
    files = result.scalars().all()

    return {
        "files": [f.to_dict() for f in files],
        "count": len(files)
    }


@router.post("/{file_id}/approve")
async def approve_file(
        file_id: int,
        admin_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Одобрить файл"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    # Находим файл
    result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
    file_obj = result.scalar_one_or_none()

    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден"
        )

    file_obj.status = "approved"
    await db.commit()

    print(f"✅ Файл одобрен: {file_obj.filename}")

    return {
        "status": "success",
        "message": f"Файл '{file_obj.filename}' одобрен",
        "file": file_obj.to_dict()
    }


@router.post("/{file_id}/reject")
async def reject_file(
        file_id: int,
        admin_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Отклонить файл"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    # Находим файл
    result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
    file_obj = result.scalar_one_or_none()

    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден"
        )

    file_obj.status = "rejected"
    await db.commit()
    await db.refresh(file_obj)

    print(f"❌ Файл отклонён: {file_obj.filename}")

    # 📢 Отправляем уведомление всем через WebSocket
    await manager.broadcast({
        "type": "file_status_update",
        "file_id": file_obj.id,
        "status": "rejected"
    })

    return {
        "status": "success",
        "message": f"Файл '{file_obj.filename}' отклонён",
        "file": file_obj.to_dict()
    }


@router.get("/approved")
async def get_approved_files(db: AsyncSession = Depends(get_db)):
    """Получить все одобренные файлы"""

    result = await db.execute(
        select(UploadedFile)
        .where(UploadedFile.status == "approved")
        .order_by(UploadedFile.created_at)
    )
    files = result.scalars().all()

    return {
        "files": [f.to_dict() for f in files]
    }


@router.get("/my-files")
async def get_my_files(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить файлы текущего пользователя (включая pending)"""

    result = await db.execute(
        select(UploadedFile)
        .where(UploadedFile.user_id == user_id)
        .order_by(UploadedFile.created_at)
    )
    files = result.scalars().all()

    return {
        "files": [f.to_dict() for f in files]
    }