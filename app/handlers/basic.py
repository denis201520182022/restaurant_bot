from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.keyboards.main import main_reply_kb, options_inline_kb
from app.db.crud import save_user_to_db
from app.utils.clear import track_message, clear_tracked_messages

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await clear_tracked_messages(state, bot, message.from_user.id)
    await save_user_to_db(message.from_user.id, message.from_user.username)
    
    await message.delete() # <-- ДОБАВЛЕНО: удаляем команду /start
    
    await message.answer(
        "Привет! Я бот Prosto_cafe 🍽️\n\n"
        "Выберите раздел ниже ",
        reply_markup=main_reply_kb()
    )
    sent_message = await message.answer(
        "Доступные опции:",
        reply_markup=options_inline_kb()
    )
    await track_message(state, sent_message)

HELP_TEXT = (
    "<b>ℹ️ Справка по боту</b>\n\n"
    "Привет! Я помогу вам взаимодействовать с нашим рестораном. Вот что я умею:\n\n"
    "📋 <b>Меню</b>\n"
    "— Здесь вы можете посмотреть наше актуальное меню с описанием блюд и ценами. Идеально, чтобы выбрать что-нибудь вкусное!\n\n"
    
    "🗓️ <b>Бронь столиков</b>\n"
    "— <b>Создать бронь</b>: Вы можете забронировать столик на любой день в течение недели. Просто выберите дату, удобное время и свободный столик.\n"
    "— <b>Ваши брони</b>: Показывает список всех ваших активных броней. Вы можете легко отменить любую из них, просто нажав на соответствующую бронь и подтвердив действие.\n\n"
    
    "🛍️ <b>Предзаказ</b>\n"
    "— <b>Создать предзаказ</b>: Оформите заказ заранее, чтобы не ждать! Выберите блюдо из меню, укажите удобную дату (сегодня, завтра или послезавтра) и введите время, к которому всё должно быть готово.\n"
    "— <b>Мои предзаказы</b>: Здесь отображается список ваших будущих заказов. Если планы изменились, вы можете отменить любой предзаказ, нажав на него.\n\n"
    
    "✨ <b>Чистота в чате</b>\n"
    "Я стараюсь поддерживать порядок в нашем диалоге. Сообщения от предыдущих разделов и ваши команды будут автоматически удаляться, чтобы вы не запутались в старых кнопках.\n\n"
    "Для навигации используйте главное меню с кнопками."
)

async def send_help(event: Message | CallbackQuery, state: FSMContext, bot: Bot):
    await clear_tracked_messages(state, bot, event.from_user.id)
    
    # Если это сообщение, удаляем его
    if isinstance(event, Message):
        await event.delete() # <-- ДОБАВЛЕНО: удаляем /help или "Помощь"

    sent_message = await bot.send_message(event.from_user.id, HELP_TEXT)
    await track_message(state, sent_message)

    if isinstance(event, CallbackQuery):
        await event.answer()

# Хендлеры, вызывающие общую функцию (без изменений)
@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def help_message(message: Message, state: FSMContext, bot: Bot):
    await send_help(message, state, bot)

@router.callback_query(F.data == "cat_help")
async def help_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await send_help(callback, state, bot)

# Хендлер на кнопку "Опции" из reply-клавиатуры
@router.message(F.text == "📋 Опции")
async def show_options(message: Message, state: FSMContext, bot: Bot):
    await clear_tracked_messages(state, bot, message.from_user.id)
    
    await message.delete() # <-- ДОБАВЛЕНО: удаляем сообщение "Опции"
    
    sent_message = await message.answer("Выберите опцию:", reply_markup=options_inline_kb())
    await track_message(state, sent_message)

# Этот хендлер будет ловить кнопку "Назад" из любого раздела
@router.callback_query(F.data == "back_to_main_options")
async def back_to_main_options_handler(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает пользователя в главное меню с опциями,
    редактируя существующее сообщение.
    """
    await state.clear()
    
    # Редактируем сообщение и СОХРАНЯЕМ его в переменную
    edited_message = await callback.message.edit_text(
        "Выберите опцию:",
        reply_markup=options_inline_kb()
    )
    
    # ДОБАВЛЕНО: Снова начинаем отслеживать это сообщение
    await track_message(state, edited_message)
    
    await callback.answer()