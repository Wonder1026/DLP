from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.api.routes import messages, dlp_admin, auth, violations
from app.websocket.manager import manager
from app.database import init_db, get_db
from app.dlp.engine import dlp_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события - выполняется при старте и остановке"""
    # Startup
    print("🚀 Запуск приложения...")
    await init_db()
    print("✅ База данных инициализирована")
    print(f"🛡️ DLP система активна. Запрещённые слова: {dlp_engine.text_analyzer.get_keywords()}")
    yield
    # Shutdown
    print("👋 Остановка приложения...")


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


@app.get("/")
def root():
    """Главная страница - интерфейс мессенджера"""
    return FileResponse("static/index.html")


@app.get("/admin")
def admin():
    """Админ-панель DLP"""
    return FileResponse("static/admin.html")


@app.get("/login")
def login_page():
    """Страница входа"""
    return FileResponse("static/login.html")


@app.get("/profile")
def profile_page():
    """Личный кабинет"""
    return FileResponse("static/profile.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time сообщений"""
    await manager.connect(websocket)

    # Получаем данные пользователя из первого сообщения
    user_data = None

    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_json()

            # Если это первое сообщение, получаем user_id
            if 'user_id' in data and not user_data:
                user_data = data

            user_id = data.get("user_id")
            user = data.get("user", "Аноним")
            text = data.get("text", "")

            print(f"📨 Получено сообщение от {user}: {text}")

            # Проверяем, не забанен ли пользователь
            if user_id:
                from app.database import AsyncSessionLocal
                from sqlalchemy import select
                from app.models.user import User

                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(User).where(User.id == user_id))
                    user_obj = result.scalar_one_or_none()

                    if user_obj and user_obj.is_banned:
                        await websocket.send_json({
                            "type": "error",
                            "message": "❌ Вы заблокированы администратором и не можете отправлять сообщения"
                        })
                        continue

            # 🛡️ ПРОВЕРКА DLP
            dlp_result = dlp_engine.check_message(text, user)

            if not dlp_result["allowed"]:
                # Сообщение заблокировано!
                print(f"🚫 Сообщение заблокировано: {dlp_result['reason']}")

                # 🚨 СОХРАНЯЕМ НАРУШЕНИЕ В БД
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

                # Отправляем уведомление только отправителю
                await websocket.send_json({
                    "type": "error",
                    "message": f"❌ {dlp_result['reason']}"
                })
                continue

            # Сообщение разрешено - сохраняем в БД
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await manager.save_message(db=db, user=user, text=text)

            # Отправляем всем подключенным клиентам
            await manager.broadcast({
                "type": "message",
                "user": user,
                "text": text,
                "timestamp": data.get("timestamp", "")
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "dlp_active": True,
        "forbidden_keywords_count": len(dlp_engine.text_analyzer.get_keywords())
    }