from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse
from app.utils.security import hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""

    # Проверяем, существует ли пользователь
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким username уже существует"
        )

    # Создаём нового пользователя
    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        display_name=user_data.display_name,
        is_admin=False  # По умолчанию не админ
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    print(f"✅ Зарегистрирован новый пользователь: {new_user.username}")

    return new_user


@router.post("/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Вход пользователя"""

    # Ищем пользователя
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный username или пароль"
        )

    # Проверяем пароль
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный username или пароль"
        )

    print(f"✅ Пользователь вошёл: {user.username}")

    return {
        "status": "success",
        "message": "Вход выполнен успешно",
        "user": user.to_dict()
    }


@router.get("/me")
async def get_current_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить информацию о текущем пользователе"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    return user.to_dict()


@router.put("/profile")
async def update_profile(
        user_id: int,
        display_name: str = None,
        db: AsyncSession = Depends(get_db)
):
    """Обновление профиля пользователя"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Обновляем имя если передано
    if display_name:
        user.display_name = display_name

    await db.commit()
    await db.refresh(user)

    print(f"✅ Профиль обновлён: {user.username}")

    return {
        "status": "success",
        "message": "Профиль обновлён",
        "user": user.to_dict()
    }


@router.post("/make-admin")
async def make_admin(
        admin_id: int,
        target_username: str,
        db: AsyncSession = Depends(get_db)
):
    """Назначить пользователя администратором (только для админов)"""

    # Проверяем, что запрос делает админ
    result = await db.execute(
        select(User).where(User.id == admin_id)
    )
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    # Ищем целевого пользователя
    result = await db.execute(
        select(User).where(User.username == target_username)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь {target_username} не найден"
        )

    if target_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь {target_username} уже является администратором"
        )

    # Назначаем администратором
    target_user.is_admin = True
    await db.commit()
    await db.refresh(target_user)

    print(f"✅ Пользователь {target_username} назначен администратором")

    return {
        "status": "success",
        "message": f"Пользователь {target_username} назначен администратором",
        "user": target_user.to_dict()
    }


@router.get("/users")
async def get_all_users(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Получить список всех пользователей (только для админов)"""

    # Проверяем, что запрос делает админ
    result = await db.execute(
        select(User).where(User.id == admin_id)
    )
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для администраторов."
        )

    # Получаем всех пользователей
    result = await db.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()

    return {
        "users": [user.to_dict() for user in users]
    }


@router.post("/remove-admin")
async def remove_admin(
        super_admin_id: int,
        target_user_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Снять права администратора (только для супер-админа)"""

    # Проверяем, что запрос делает супер-админ
    result = await db.execute(
        select(User).where(User.id == super_admin_id)
    )
    super_admin = result.scalar_one_or_none()

    if not super_admin or not super_admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Только для главного администратора."
        )

    # Ищем целевого пользователя
    result = await db.execute(
        select(User).where(User.id == target_user_id)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    if target_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя снять права у главного администратора"
        )

    if not target_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не является администратором"
        )

    # Снимаем права администратора
    target_user.is_admin = False
    await db.commit()
    await db.refresh(target_user)

    print(f"✅ У пользователя {target_user.username} сняты права администратора")

    return {
        "status": "success",
        "message": f"Права администратора у {target_user.username} сняты",
        "user": target_user.to_dict()
    }