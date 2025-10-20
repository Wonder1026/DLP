from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Corporate Messenger"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
