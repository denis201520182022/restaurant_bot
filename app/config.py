from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    BASE_WEBHOOK_URL: str

    PORT: int = Field(default=8080)
    
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    db_host: str = Field(..., alias="DB_HOST")
    db_port: int = Field(..., alias="DB_PORT")
    db_name: str = Field(..., alias="DB_NAME")
    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # игнорируем незадекларированные переменные
        populate_by_name=True  # разрешаем db_host <-> DB_HOST
    )


settings = Settings()
