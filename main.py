from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.api.routes import messages
from app.websocket.manager import manager
from app.database import init_db, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события - выполняется при старте и остановке"""
    # Startup
    print("🚀 Запуск приложения...")
    await init_db()
    print("✅ База данных инициализирована")
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

# Подключаем роутер для сообщений
app.include_router(
    messages.router,
    prefix="/api/messages",
    tags=["messages"]
)


@app.get("/")
def root():
    """Главная страница - интерфейс мессенджера"""
    return FileResponse("static/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time сообщений"""
    await manager.connect(websocket)

    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_json()

            print(f"📨 Получено сообщение: {data}")

            # Сохраняем в БД
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await manager.save_message(
                    db=db,
                    user=data.get("user", "Аноним"),
                    text=data.get("text", "")
                )

            # Отправляем всем подключенным клиентам
            await manager.broadcast({
                "user": data.get("user", "Аноним"),
                "text": data.get("text", ""),
                "timestamp": data.get("timestamp", "")
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
def health():
    return {"status": "ok"}