# app/db/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.db.session import Base
import datetime
# ДОБАВЬТЕ ЭТОТ ИМПОРТ
from sqlalchemy.sql import func


# Пользователи
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    # ИЗМЕНЕНО: Добавлено timezone=True
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


# Меню (без изменений)
class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Integer, nullable=False)
    # НОВОЕ ПОЛЕ для ID фото в Telegram
    image_id = Column(String, nullable=True)


# Бронь столиков
class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    # ИЗМЕНЕНО: Добавлено timezone=True
    datetime = Column(DateTime(timezone=True), nullable=False)
    guests = Column(Integer, nullable=False)
    contact = Column(String, nullable=False)
    table_number = Column(Integer, nullable=False)
    user = relationship("User")


# Предзаказы
class Preorder(Base):
    __tablename__ = "preorders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, nullable=False)
    # ИЗМЕНЕНО: Добавлено timezone=True и server_default для консистентности
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # ИЗМЕНЕНО: Добавлено timezone=True
    ready_at = Column(DateTime(timezone=True), nullable=False)
    user = relationship("User")
    item = relationship("MenuItem")