from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.security import hash_password


async def create_super_admin_if_not_exists(db: AsyncSession):
    """Создать супер-администратора если его нет"""

    # Проверяем, есть ли уже супер-админ
    result = await db.execute(
        select(User).where(User.is_super_admin == True)
    )
    existing_super_admin = result.scalar_one_or_none()

    if existing_super_admin:
        print(f"✓ Супер-админ уже существует: {existing_super_admin.username}")
        return existing_super_admin

    # Создаём супер-админа
    super_admin = User(
        username="superadmin",
        password_hash=hash_password("superadmin"),
        display_name="Главный Администратор",
        is_admin=True,
        is_super_admin=True,
        is_banned=False
    )

    db.add(super_admin)
    await db.commit()
    await db.refresh(super_admin)

    print("=" * 60)
    print("🎉 СУПЕР-АДМИНИСТРАТОР СОЗДАН!")
    print("=" * 60)
    print(f"   Username: superadmin")
    print(f"   Password: superadmin")
    print(f"   ⚠️  ВАЖНО: Смените пароль после первого входа!")
    print("=" * 60)

    return super_admin


async def initialize_default_data(db: AsyncSession):
    """Инициализация начальных данных"""
    await create_super_admin_if_not_exists(db)
    # Здесь можно добавить другие начальные данные