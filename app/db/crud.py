from sqlalchemy import select, delete
from app.db.session import get_session
from datetime import datetime, date, timedelta
from app.db.models import User, MenuItem, Booking, Preorder
from sqlalchemy.orm import selectinload

# ========================
# Пользователи
# ========================
async def save_user_to_db(tg_id: int, username: str = None):
    async with get_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            new_user = User(tg_id=tg_id, username=username)
            session.add(new_user)
            await session.commit()


# ========================
# Меню
# ========================
async def get_menu_items():
    async with get_session() as session:
        result = await session.execute(select(MenuItem))
        return result.scalars().all()


# ========================
# Проверка доступных столиков
# ========================
async def get_available_tables(booking_date: str, booking_time: str, all_tables: list[int]) -> list[int]:
    """
    Возвращает список свободных столиков на УКАЗАННЫЕ ДАТУ И ВРЕМЯ.
    booking_date: строка вида "YYYY-MM-DD"
    booking_time: строка вида "HH:MM"
    """
    async with get_session() as session:
        # Собираем полную дату-время из двух строк
        dt_str = f"{booking_date} {booking_time}"
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

        result = await session.execute(
            select(Booking.table_number).where(Booking.datetime == dt_obj)
        )
        booked_tables = [b[0] for b in result.all()]
        return [t for t in all_tables if t not in booked_tables]

# ========================
# Создание брони
# ========================
async def create_booking(tg_id: int, table_number: int, booking_date: str, booking_time: str, contact: str):
    async with get_session() as session:
        # Собираем полную дату-время из двух строк
        dt_str = f"{booking_date} {booking_time}"
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one() # Предполагаем, что юзер уже есть

        booking = Booking(
            user_id=user.id,
            table_number=table_number,
            datetime=dt_obj,
            guests=1,
            contact=contact
        )
        session.add(booking)
        await session.commit()



# ========================
# Получение броней пользователя
# ========================
async def get_user_bookings(tg_id: int):
    async with get_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return []

        # Сортируем по дате для удобства
        result = await session.execute(
            select(Booking).where(Booking.user_id == user.id).order_by(Booking.datetime)
        )
        return result.scalars().all()

# ========================
# Отмена брони
# ========================
async def cancel_booking(booking_id: int):
    async with get_session() as session:
        result = await session.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()
        if booking:
            await session.delete(booking)
            await session.commit()


# ========================
# Предзаказы
# ========================
async def create_preorder(tg_id: int, item_id: int, quantity: int, ready_date: str, ready_time: str):
    async with get_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one()

        # Собираем полную дату-время из двух строк
        dt_str = f"{ready_date} {ready_time}"
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

        preorder = Preorder(
            user_id=user.id,
            item_id=item_id,
            quantity=quantity,
            ready_at=dt_obj
        )
        session.add(preorder)
        await session.commit()

# ========================
# Получение предзаказов пользователя
# ========================
async def get_user_preorders(tg_id: int):
    async with get_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return []

        # Получаем предзаказы и сразу подгружаем связанные с ними MenuItem
        # чтобы избежать дополнительных запросов в цикле. Сортируем по дате.
        result = await session.execute(
            select(Preorder)
            .where(Preorder.user_id == user.id)
            .options(selectinload(Preorder.item))
            .order_by(Preorder.ready_at)
        )
        return result.scalars().all()
    
# ========================
# Отмена предзаказа
# ========================
async def cancel_preorder(preorder_id: int):
    async with get_session() as session:
        # Находим предзаказ по его ID
        result = await session.execute(select(Preorder).where(Preorder.id == preorder_id))
        preorder = result.scalar_one_or_none()
        if preorder:
            # Если найден - удаляем и сохраняем изменения
            await session.delete(preorder)
            await session.commit()


# ========================
# Получение одного блюда по ID
# ========================
async def get_menu_item_by_id(item_id: int):
    async with get_session() as session:
        result = await session.execute(select(MenuItem).where(MenuItem.id == item_id))
        return result.scalar_one_or_none()
    



# ========================
# Получение предстоящих броней для уведомления
# ========================
async def get_upcoming_bookings(start_time: datetime, end_time: datetime):
    async with get_session() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.datetime.between(start_time, end_time))
            .options(selectinload(Booking.user))
        )
        return result.scalars().all()

# ========================
# Получение предстоящих предзаказов для уведомления
# ========================
async def get_upcoming_preorders(start_time: datetime, end_time: datetime):
    async with get_session() as session:
        result = await session.execute(
            select(Preorder)
            .where(Preorder.ready_at.between(start_time, end_time))
            .options(selectinload(Preorder.item), selectinload(Preorder.user))
        )
        return result.scalars().all()