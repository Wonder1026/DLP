from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# SQLite база данных (файл создастся автоматически)
DATABASE_URL = "sqlite+aiosqlite:///./messenger.db"

# Создаём движок базы данных
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Логирование SQL запросов
    future=True
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()


async def get_db():
    """Получение сессии БД"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Создание таблиц в БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
