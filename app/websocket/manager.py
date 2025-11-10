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
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"❌ Клиент отключен. Всего подключений: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Отправка сообщения всем подключенным клиентам"""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except RuntimeError as e:
                # WebSocket уже закрыт
                print(f"⚠️ Не удалось отправить сообщение (соединение закрыто): {e}")
                disconnected.append(connection)
            except Exception as e:
                print(f"⚠️ Ошибка отправки сообщения: {e}")
                disconnected.append(connection)

        # Удаляем отключенные соединения
        for conn in disconnected:
            self.disconnect(conn)

    async def save_message(self, db: AsyncSession, user: str, text: str):
        """Сохранение сообщения в БД"""
        message = Message(user=user, text=text)
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    async def save_violation(self, db: AsyncSession, user_id: int, username: str,
                             display_name: str, message_text: str, found_keywords: list):
        """Сохранение нарушения в БД"""
        from app.models.violation import Violation

        violation = Violation(
            user_id=user_id,
            username=username,
            display_name=display_name,
            message_text=message_text,
            found_keywords=','.join(found_keywords) if found_keywords else '',
            violation_type="keyword",
            is_reviewed=False
        )

        db.add(violation)
        await db.commit()
        await db.refresh(violation)

        print(f"🚨 Нарушение зафиксировано: {username} - {found_keywords}")

        return violation


manager = ConnectionManager()