# app/scheduler.py

import logging
from datetime import datetime, timedelta
import pytz
from aiogram import Bot

from app.db.crud import get_upcoming_bookings, get_upcoming_preorders

async def check_reminders(bot: Bot):
    """
    Проверяет базу данных на наличие предстоящих событий и отправляет уведомления.
    """
    # Часовой пояс UTC, по которому работает вся система
    utc_tz = pytz.UTC
    # Часовой пояс пользователя (например, Москва). Замени на свой, если нужно.
    # Список всех поясов: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    user_tz = pytz.timezone("Europe/Moscow")

    now_utc = datetime.now(utc_tz)

    # --- Проверка броней (за 1.5 часа = 90 минут) ---
    booking_start_time = now_utc + timedelta(minutes=90)
    booking_end_time = booking_start_time + timedelta(minutes=1)
    
    upcoming_bookings = await get_upcoming_bookings(booking_start_time, booking_end_time)
    for booking in upcoming_bookings:
        user_tg_id = booking.user.tg_id
        
        # КОНВЕРТАЦИЯ ВРЕМЕНИ ДЛЯ ПОЛЬЗОВАТЕЛЯ
        booking_time_local = booking.datetime.astimezone(user_tz)
        
        text = (
            f"🔔 <b>Напоминание о брони!</b>\n\n"
            f"Вы забронировали столик №{booking.table_number} на "
            # Используем локальное время для отображения
            f"<b>{booking_time_local.strftime('%d.%m.%Y в %H:%M')}</b>.\n\n"
            f"Ждём вас!"
        )
        try:
            await bot.send_message(chat_id=user_tg_id, text=text, parse_mode="HTML")
            logging.info(f"Sent booking reminder to {user_tg_id}")
        except Exception as e:
            logging.error(f"Failed to send booking reminder to {user_tg_id}: {e}")

    # --- Проверка предзаказов (за 30 минут) ---
    preorder_start_time = now_utc + timedelta(minutes=30)
    preorder_end_time = preorder_start_time + timedelta(minutes=1)

    upcoming_preorders = await get_upcoming_preorders(preorder_start_time, preorder_end_time)
    for preorder in upcoming_preorders:
        user_tg_id = preorder.user.tg_id

        # КОНВЕРТАЦИЯ ВРЕМЕНИ ДЛЯ ПОЛЬЗОВАТЕЛЯ
        preorder_time_local = preorder.ready_at.astimezone(user_tz)

        text = (
            f"🔔 <b>Напоминание о предзаказе!</b>\n\n"
            f"Ваш заказ на '{preorder.item.title}' ({preorder.quantity} шт.) "
            # Используем локальное время для отображения
            f"будет готов через 30 минут в <b>{preorder_time_local.strftime('%H:%M')}</b>.\n\n"
            f"Приятного аппетита!"
        )
        try:
            await bot.send_message(chat_id=user_tg_id, text=text, parse_mode="HTML")
            logging.info(f"Sent preorder reminder to {user_tg_id}")
        except Exception as e:
            logging.error(f"Failed to send preorder reminder to {user_tg_id}: {e}")