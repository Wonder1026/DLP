from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """Схема для регистрации"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)
    display_name: str = Field(..., min_length=2, max_length=100)


class UserLogin(BaseModel):
    """Схема для входа"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя"""
    id: int
    username: str
    display_name: str
    avatar: str | None
    is_admin: bool

    class Config:
        from_attributes = True