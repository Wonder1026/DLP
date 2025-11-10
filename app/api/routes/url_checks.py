from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.url_check import URLCheck
import json

router = APIRouter()


@router.get("/pending")
async def get_pending_urls(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Получить URL на проверке (только для админов)"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    # Получаем URL на проверке
    result = await db.execute(
        select(URLCheck)
        .where(URLCheck.status == "pending")
        .order_by(URLCheck.created_at.desc())
    )
    urls = result.scalars().all()

    return {
        "urls": [u.to_dict() for u in urls],
        "count": len(urls)
    }


@router.get("/all")
async def get_all_urls(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Получить все проверки URL (только для админов)"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    # Получаем все URL
    result = await db.execute(
        select(URLCheck).order_by(URLCheck.created_at.desc())
    )
    urls = result.scalars().all()

    return {
        "urls": [u.to_dict() for u in urls],
        "count": len(urls)
    }


@router.post("/{url_check_id}/scan")
async def scan_url_virustotal(
        url_check_id: int,
        admin_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Проверить URL через VirusTotal и автоматически опубликовать/заблокировать"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    # Находим URL проверку
    result = await db.execute(select(URLCheck).where(URLCheck.id == url_check_id))
    url_check = result.scalar_one_or_none()

    if not url_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL проверка не найдена"
        )

    # Проверяем через VirusTotal
    from app.services.virustotal_service import virustotal_service
    import json

    vt_result = await virustotal_service.scan_url(url_check.url)

    # Сохраняем результат
    url_check.virustotal_result = json.dumps(vt_result, ensure_ascii=False)
    url_check.is_reviewed = True

    # Автоматически определяем статус
    if vt_result.get("status") == "clean":
        url_check.status = "safe"
        print(f"✅ URL безопасен (VirusTotal): {url_check.url}")

        # Публикуем сообщение в чат
        from app.websocket.manager import manager

        await manager.save_message(db=db, user=url_check.display_name, text=url_check.message_text)

        await manager.broadcast({
            "type": "message",
            "user": url_check.display_name,
            "text": url_check.message_text,
            "timestamp": url_check.created_at.strftime("%H:%M:%S")
        })

        await manager.broadcast({
            "type": "info",
            "message": f"✅ Сообщение со ссылкой проверено и опубликовано (VirusTotal)"
        })

    elif vt_result.get("status") == "malicious":
        url_check.status = "malicious"
        print(f"⚠️ URL опасен (VirusTotal): {url_check.url}")

        from app.websocket.manager import manager

        await manager.broadcast({
            "type": "warning",
            "message": f"⚠️ Сообщение заблокировано: обнаружена опасная ссылка (VirusTotal)"
        })

    elif vt_result.get("status") == "suspicious":
        url_check.status = "suspicious"
        print(f"⚠️ URL подозрителен (VirusTotal): {url_check.url}")

    await db.commit()
    await db.refresh(url_check)

    return {
        "status": "success",
        "message": "Проверка URL завершена",
        "virustotal_result": vt_result,
        "url_check": url_check.to_dict(),
        "auto_published": url_check.status == "safe"
    }


@router.post("/{url_check_id}/mark-safe")
async def mark_url_safe(
        url_check_id: int,
        admin_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Отметить URL как безопасный и опубликовать сообщение"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    # Находим URL проверку
    result = await db.execute(select(URLCheck).where(URLCheck.id == url_check_id))
    url_check = result.scalar_one_or_none()

    if not url_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL проверка не найдена"
        )

    url_check.status = "safe"
    url_check.is_reviewed = True

    await db.commit()
    await db.refresh(url_check)

    print(f"✅ URL одобрен: {url_check.url}")

    # Публикуем сообщение в чат
    from app.websocket.manager import manager

    # Сохраняем сообщение в БД
    await manager.save_message(db=db, user=url_check.display_name, text=url_check.message_text)

    # Отправляем всем в чат
    await manager.broadcast({
        "type": "message",
        "user": url_check.display_name,
        "text": url_check.message_text,
        "timestamp": url_check.created_at.strftime("%H:%M:%S")
    })

    # Уведомляем пользователя
    await manager.broadcast({
        "type": "info",
        "message": f"✅ Ваше сообщение со ссылкой было одобрено администратором"
    })

    return {
        "status": "success",
        "message": f"URL '{url_check.url}' одобрен и сообщение опубликовано",
        "url_check": url_check.to_dict()
    }


@router.post("/{url_check_id}/mark-malicious")
async def mark_url_malicious(
        url_check_id: int,
        admin_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Отметить URL как опасный (ручная проверка)"""

    # Проверяем права админа
    result = await db.execute(select(User).where(User.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён"
        )

    # Находим URL проверку
    result = await db.execute(select(URLCheck).where(URLCheck.id == url_check_id))
    url_check = result.scalar_one_or_none()

    if not url_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL проверка не найдена"
        )

    url_check.status = "malicious"
    url_check.is_reviewed = True

    await db.commit()
    await db.refresh(url_check)

    print(f"⚠️ URL отмечен как опасный: {url_check.url}")

    return {
        "status": "success",
        "message": f"URL '{url_check.url}' отмечен как опасный",
        "url_check": url_check.to_dict()
    }