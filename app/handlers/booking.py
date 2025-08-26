import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from app.db.crud import get_available_tables, create_booking, get_user_bookings, cancel_booking
from app.utils.clear import track_message, clear_tracked_messages

router = Router(name="booking")

ALL_TABLES = [1, 2, 3, 4, 5]
TIME_OPTIONS = ["18:00", "19:00", "20:00", "21:00"]

class BookingForm(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    choosing_table = State()
    contact = State()
    confirming_cancel = State()

# --- Клавиатуры с кнопками "Назад" ---

def booking_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Создать бронь", callback_data="create_booking"),
            InlineKeyboardButton(text="Ваши брони", callback_data="user_bookings")
        ]
    ])

def date_keyboard_booking() -> InlineKeyboardMarkup:
    buttons = []
    today = datetime.date.today()
    for i in range(7):
        day = today + datetime.timedelta(days=i)
        date_iso = day.isoformat()
        date_text = day.strftime("%d.%m (%a)")
        if i == 0: date_text = f"Сегодня, {date_text}"
        if i == 1: date_text = f"Завтра, {date_text}"
        buttons.append([InlineKeyboardButton(text=date_text, callback_data=f"book_date:{date_iso}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="cat_booking_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def time_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=t, callback_data=f"book_time:{t}")] for t in TIME_OPTIONS]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="booking_go_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def table_keyboard(tables: list[int]):
    buttons = [[InlineKeyboardButton(text=f"Столик {t}", callback_data=f"book_table:{t}")] for t in tables]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="booking_go_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_booking_keyboard(bookings):
    buttons = [[InlineKeyboardButton(
        text=f"{b.datetime.strftime('%d.%m %H:%M')} — Столик {b.table_number}",
        callback_data=f"cancel_booking:{b.id}"
    )] for b in bookings]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="cat_booking_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
    
def back_kb_booking() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="booking_go_back")]
    ])

# --- Основные хендлеры ---

@router.callback_query(F.data == "cat_booking")
async def booking_menu(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await clear_tracked_messages(state, bot, callback.from_user.id)
    sent_message = await callback.message.answer("📋 Бронирование столиков", reply_markup=booking_main_kb())
    await track_message(state, sent_message)
    await callback.answer()

@router.callback_query(F.data == "cat_booking_menu")
async def booking_menu_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    edited_message = await callback.message.edit_text("📋 Бронирование столиков", reply_markup=booking_main_kb())
    await track_message(state, edited_message)
    await callback.answer()

# --- Универсальный хендлер "Назад" для бронирования ---
@router.callback_query(F.data == "booking_go_back", StateFilter(BookingForm))
async def booking_go_back_handler(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    edited_message = None

    if current_state == BookingForm.contact:
        data = await state.get_data()
        available_tables = await get_available_tables(data['date'], data['time'], ALL_TABLES)
        edited_message = await callback.message.edit_text("Выберите столик:", reply_markup=table_keyboard(available_tables))
        await state.set_state(BookingForm.choosing_table)
    elif current_state == BookingForm.choosing_table:
        edited_message = await callback.message.edit_text("Выберите время:", reply_markup=time_keyboard())
        await state.set_state(BookingForm.choosing_time)
    elif current_state == BookingForm.choosing_time:
        edited_message = await callback.message.edit_text("Выберите дату:", reply_markup=date_keyboard_booking())
        await state.set_state(BookingForm.choosing_date)

    if edited_message:
        await track_message(state, edited_message)
    await callback.answer()

# --- Сценарий создания брони ---

@router.callback_query(F.data == "create_booking")
async def choose_date(callback: CallbackQuery, state: FSMContext):
    edited_message = await callback.message.edit_text("Выберите дату:", reply_markup=date_keyboard_booking())
    await track_message(state, edited_message)
    await state.set_state(BookingForm.choosing_date)
    await callback.answer()

@router.callback_query(F.data.startswith("book_date:"), BookingForm.choosing_date)
async def date_chosen(callback: CallbackQuery, state: FSMContext):
    await state.update_data(date=callback.data.split(":")[1])
    edited_message = await callback.message.edit_text("Выберите время:", reply_markup=time_keyboard())
    await track_message(state, edited_message)
    await state.set_state(BookingForm.choosing_time)
    await callback.answer()

@router.callback_query(F.data.startswith("book_time:"), BookingForm.choosing_time)
async def time_chosen(callback: CallbackQuery, state: FSMContext):
    selected_time = callback.data.replace("book_time:", "")
    data = await state.get_data()
    selected_date = data['date']
    await state.update_data(time=selected_time)
    
    available_tables = await get_available_tables(selected_date, selected_time, ALL_TABLES)
    if not available_tables:
        edited_message = await callback.message.edit_text(f"На {selected_date} {selected_time} все столики заняты. Пожалуйста, выберите другое время.", reply_markup=time_keyboard())
        await track_message(state, edited_message)
        return

    edited_message = await callback.message.edit_text("Выберите столик:", reply_markup=table_keyboard(available_tables))
    await track_message(state, edited_message)
    await state.set_state(BookingForm.choosing_table)
    await callback.answer()

@router.callback_query(F.data.startswith("book_table:"), BookingForm.choosing_table)
async def table_chosen(callback: CallbackQuery, state: FSMContext):
    await state.update_data(table_number=int(callback.data.split(":")[1]))
    edited_message = await callback.message.edit_text("Введите ваше имя и телефон для подтверждения брони:", reply_markup=back_kb_booking())
    await track_message(state, edited_message)
    await state.set_state(BookingForm.contact)
    await callback.answer()

@router.message(BookingForm.contact, F.text)
async def enter_contact(message: Message, state: FSMContext, bot: Bot):
    await clear_tracked_messages(state, bot, message.from_user.id)
    await message.delete()
    data = await state.get_data()
    await create_booking(
        tg_id=message.from_user.id,
        table_number=data["table_number"],
        booking_date=data["date"],
        booking_time=data["time"],
        contact=message.text.strip()
    )
    await message.answer(
        f"✅ Ваша бронь сохранена!\n\n"
        f"<b>Дата и время: {data['date']} {data['time']}</b>\n"
        f"Столик: {data['table_number']}\n"
        f"Контакт: {message.text.strip()}"
    )
    await state.clear()

# --- Сценарий просмотра и отмены броней ---
async def show_user_bookings(callback: CallbackQuery, state: FSMContext):
    bookings = await get_user_bookings(callback.from_user.id)
    text = "У вас пока нет броней."
    reply_markup = None
    if bookings:
        text = "Ваши брони (нажмите, чтобы отменить):"
        reply_markup = cancel_booking_keyboard(bookings)
    
    edited_message = await callback.message.edit_text(text, reply_markup=reply_markup)
    await track_message(state, edited_message)
    await callback.answer()

@router.callback_query(F.data == "user_bookings")
async def user_bookings_handler(callback: CallbackQuery, state: FSMContext):
    await show_user_bookings(callback, state)

@router.callback_query(F.data.startswith("cancel_booking:"))
async def confirm_cancel(callback: CallbackQuery, state: FSMContext):
    await state.update_data(cancel_id=int(callback.data.split(":")[1]))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да, отменить", callback_data="confirm_cancel"),
            InlineKeyboardButton(text="Нет", callback_data="deny_cancel")
        ]
    ])
    await callback.message.edit_text("Вы уверены, что хотите отменить бронь?", reply_markup=kb)
    await state.set_state(BookingForm.confirming_cancel)
    await callback.answer()

@router.callback_query(F.data == "confirm_cancel", BookingForm.confirming_cancel)
async def do_cancel(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await cancel_booking(data["cancel_id"])
    await state.clear()
    await callback.answer("Бронь отменена!", show_alert=True)
    # После отмены редактируем сообщение, чтобы показать обновленный список
    await show_user_bookings(callback, state)

@router.callback_query(F.data == "deny_cancel", BookingForm.confirming_cancel)
async def deny_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_user_bookings(callback, state)