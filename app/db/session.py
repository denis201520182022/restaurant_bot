from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from app.config import settings



# URL для подключения
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

# Движок
engine = create_async_engine(DATABASE_URL, echo=True)

# Сессия
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Асинхронный генератор сессий
@asynccontextmanager
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
# Базовый класс для моделей
class Base(DeclarativeBase):
    pass
