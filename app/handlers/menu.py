from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from app.db.crud import get_menu_items
from app.utils.clear import track_message, clear_tracked_messages

router = Router(name="menu")

def back_to_main_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура с одной кнопкой 'Назад' в главное меню."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_options")]
    ])


@router.callback_query(F.data == "cat_menu")
async def menu_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # 1. Удаляем предыдущее сообщение
    await clear_tracked_messages(state, bot, callback.from_user.id)
    await callback.answer()

    items = await get_menu_items()
    
    # 2. Собираем всё меню в одно сообщение
    if not items:
        text = "📋 Меню пока пустое."
    else:
        text = "<b>📋 Наше меню:</b>\n\n"
        for item in items:
            # ИСПОЛЬЗУЕМ BLOCKQUOTE ДЛЯ ОПИСАНИЯ
            text += f"<b>{item.title} — {item.price}₽</b>\n"
            text += f"<blockquote>{item.description}</blockquote>\n\n" # <-- ВОТ ОНО, ЕПТА
    
    # 3. Отправляем одно сообщение
    sent_message = await bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=back_to_main_menu_kb(),
        parse_mode="HTML"
    )
        
    # 4. Начинаем его отслеживать
    await track_message(state, sent_message)