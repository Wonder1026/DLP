from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.api.routes import messages, dlp_admin, auth, violations, files, url_checks
from app.websocket.manager import manager
from app.database import init_db
from app.dlp.engine import dlp_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события - выполняется при старте и остановке"""
    # Startup
    print("🚀 Запуск приложения...")

    # Инициализация БД
    await init_db()
    print("✅ База данных инициализирована")

    # Инициализация начальных данных
    from app.database import AsyncSessionLocal
    from app.init_data import initialize_default_data

    async with AsyncSessionLocal() as db:
        await initialize_default_data(db)

    print(f"🛡️ DLP система активна. Запрещённые слова: {dlp_engine.text_analyzer.get_keywords()}")
    print("\n" + "=" * 60)
    print("✨ Сервер готов к работе!")
    print("   📱 Откройте: http://localhost:8000")
    print("   📚 API docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")

    yield

    # Shutdown
    print("\n👋 Остановка приложения...")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем роутеры
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["auth"]
)

app.include_router(
    messages.router,
    prefix="/api/messages",
    tags=["messages"]
)

app.include_router(
    dlp_admin.router,
    prefix="/api/dlp",
    tags=["dlp-admin"]
)

app.include_router(
    violations.router,
    prefix="/api/violations",
    tags=["violations"]
)

app.include_router(
    files.router,
    prefix="/api/files",
    tags=["files"]
)

app.include_router(
    url_checks.router,
    prefix="/api/url-checks",
    tags=["url-checks"]
)


@app.get("/")
def root():
    """Главная страница - интерфейс мессенджера"""
    return FileResponse("static/index.html")


@app.get("/login")
def login_page():
    """Страница входа"""
    return FileResponse("static/login.html")


@app.get("/admin")
def admin():
    """Админ-панель DLP"""
    return FileResponse("static/admin.html")


@app.get("/profile")
def profile_page():
    """Личный кабинет"""
    return FileResponse("static/profile.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time сообщений"""
    print("\n🔌 Новое WebSocket подключение")
    await manager.connect(websocket)

    try:
        while True:
            print("⏳ Ожидание сообщения...")
            data = await websocket.receive_json()
            print(f"✅ ПОЛУЧЕНЫ ДАННЫЕ: {data}")

            user_id = data.get("user_id")
            user = data.get("user", "Аноним")

            # Обработка файлов
            if data.get("type") == "file":
                print(f"📎 Файл от {user}")
                await manager.broadcast({
                    "type": "file",
                    "user_id": user_id,
                    "username": data.get("username"),
                    "user": user,
                    "file": data.get("file")
                })
                continue

            text = data.get("text", "")
            print(f"\n📨 Сообщение от {user}: '{text}'")

            # Проверка бана
            if user_id:
                from app.database import AsyncSessionLocal
                from sqlalchemy import select
                from app.models.user import User

                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(User).where(User.id == user_id))
                    user_obj = result.scalar_one_or_none()

                    if user_obj and user_obj.is_banned:
                        print(f"🚫 Пользователь {user} забанен")
                        await websocket.send_json({
                            "type": "error",
                            "message": "❌ Вы заблокированы"
                        })
                        continue

            # DLP проверка
            print(f"🛡️ Проверка DLP...")
            dlp_result = dlp_engine.check_message(text, user)
            print(
                f"[DLP] allowed={dlp_result['allowed']}, status={dlp_result['status']}, register={dlp_result.get('register_violation')}")

            # Блокируем только запрещённые слова
            if dlp_result["status"] == "block":
                print(f"🚫 БЛОКИРУЕМ по ключевым словам")

                if user_id:
                    from app.database import AsyncSessionLocal
                    async with AsyncSessionLocal() as db:
                        await manager.save_violation(
                            db=db,
                            user_id=user_id,
                            username=data.get("username", "unknown"),
                            display_name=user,
                            message_text=text,
                            found_keywords=dlp_result.get("found_keywords", [])
                        )

                await websocket.send_json({
                    "type": "error",
                    "message": f"❌ {dlp_result['reason']}"
                })
                continue

            # Обработка конфиденциальных данных
            if dlp_result.get("register_violation") and user_id:
                print(f"⚠️ РЕГИСТРИРУЕМ нарушение (конфиденциальные данные)")

                from app.database import AsyncSessionLocal
                from app.services.violation_service import violation_service

                async with AsyncSessionLocal() as db:
                    found_items = []
                    if dlp_result.get("sensitive_data"):
                        sensitive_items = [
                            f"{item['name']}: {item['value']}"
                            for item in dlp_result["sensitive_data"]["found_data"]
                        ]
                        found_items.extend(sensitive_items)
                        print(f"   Найдено: {found_items}")

                    await manager.save_violation(
                        db=db,
                        user_id=user_id,
                        username=data.get("username", "unknown"),
                        display_name=user,
                        message_text=text,
                        found_keywords=found_items
                    )

                    violation_result = await violation_service.register_violation(
                        db=db,
                        user_id=user_id,
                        message_text=text,
                        found_items=found_items
                    )

                    print(f"📊 Карма: {violation_result['violation_count']}/10")

                    await websocket.send_json({
                        "type": "warning",
                        "message": f"⚠️ {dlp_result['reason']}\nНарушений: {violation_result['violation_count']}/10"
                    })

                    if violation_result["should_notify_admin"]:
                        print(f"🚨 Отправляем уведомление админам! is_banned={violation_result['is_banned']}")
                        await manager.broadcast({
                            "type": "admin_notification",
                            "notification_type": "user_banned" if violation_result[
                                "is_banned"] else "violation_warning",
                            "user_id": violation_result["user_id"],
                            "username": violation_result["username"],
                            "display_name": violation_result["display_name"],
                            "violation_count": violation_result["violation_count"],
                            "is_banned": violation_result["is_banned"],
                            "message": f"🚨 Пользователь {violation_result['display_name']} {'ЗАБЛОКИРОВАН' if violation_result['is_banned'] else f'имеет {violation_result['violation_count']} нарушений'}!"
                        })

            # Обработка URL (требуется проверка)
            if dlp_result.get("status") == "url_check_required" and user_id:
                print(f"🔗 Обнаружены URL, требуется проверка")

                from app.database import AsyncSessionLocal
                from app.models.url_check import URLCheck
                import json

                async with AsyncSessionLocal() as db:
                    urls = dlp_result.get("urls", {}).get("urls", [])

                    for url in urls:
                        # Сохраняем URL на проверку
                        url_check = URLCheck(
                            url=url,
                            user_id=user_id,
                            username=data.get("username", "unknown"),
                            display_name=user,
                            message_text=text,
                            status="pending"
                        )
                        db.add(url_check)

                    await db.commit()
                    print(f"   Сохранено {len(urls)} URL на проверку")

                # Отправляем предупреждение пользователю
                await websocket.send_json({
                    "type": "info",
                    "message": f"🔗 Обнаружено ссылок: {len(urls)}. Отправлены на проверку."
                })


            # Сохраняем и отправляем сообщение
            print(f"✅ Сохраняем и отправляем сообщение")

            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await manager.save_message(db=db, user=user, text=text)

            await manager.broadcast({
                "type": "message",
                "user": user,
                "text": text,
                "timestamp": data.get("timestamp", "")
            })
            print(f"✉️ Сообщение отправлено всем\n")

    except WebSocketDisconnect:
        print("❌ WebSocket отключен")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"💥 Ошибка в WebSocket: {e}")
        import traceback
        traceback.print_exc()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "dlp_active": True,
        "forbidden_keywords_count": len(dlp_engine.text_analyzer.get_keywords())
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )