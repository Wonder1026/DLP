from fastapi import WebSocket
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message


class ConnectionManager:
    """Менеджер WebSocket соединений"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Подключение нового клиента"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Клиент подключен. Всего подключений: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Отключение клиента"""
        self.active_connections.remove(websocket)
        print(f"❌ Клиент отключен. Всего подключений: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Отправка сообщения всем подключенным клиентам"""
        for connection in self.active_connections:
            await connection.send_json(message)

    async def save_message(self, db: AsyncSession, user: str, text: str):
        """Сохранение сообщения в БД"""
        message = Message(user=user, text=text)
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message


manager = ConnectionManager()