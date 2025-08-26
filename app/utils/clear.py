# app/utils/clear.py

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

# app/utils/clear.py

# ... (остальной код файла без изменений) ...

async def track_message(state: FSMContext, message: Message):
    """
    Сохраняет ID одного сообщения для последующего удаления,
    полностью заменяя предыдущее значение.
    """
    # Теперь мы не добавляем, а просто сохраняем ID одного сообщения
    await state.update_data(message_to_delete=message.message_id)

async def clear_tracked_messages(state: FSMContext, bot: Bot, chat_id: int):
    """
    Удаляет одно отслеживаемое сообщение и очищает FSM.
    """
    data = await state.get_data()
    # Получаем один ID, а не список
    message_id = data.get('message_to_delete')

    if message_id:
        try:
            await bot.delete_message(chat_id, message_id)
        except TelegramBadRequest:
            pass # Игнорируем ошибки, если сообщение уже удалено
    
    # Сбрасываем значение в состоянии
    await state.update_data(message_to_delete=None)