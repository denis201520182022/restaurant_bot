import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.db.crud import get_menu_items, create_preorder, get_menu_item_by_id, get_user_preorders, cancel_preorder
from app.utils.clear import track_message, clear_tracked_messages

router = Router(name="preorder")

class PreorderFSM(StatesGroup):
    choosing_item = State()
    choosing_date = State()
    choosing_time = State()
    entering_quantity = State()
    confirming_cancel = State()

# --- Клавиатуры ---

def preorder_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Создать предзаказ", callback_data="create_preorder"),
            InlineKeyboardButton(text="Мои предзаказы", callback_data="user_preorders")
        ]
    ])

def preorders_list_keyboard(preorders: list) -> InlineKeyboardMarkup:
    buttons = []
    for order in preorders:
        button_text = f"{order.item.title} ({order.quantity}шт) на {order.ready_at.strftime('%d.%m %H:%M')}"
        buttons.append([
            InlineKeyboardButton(text=button_text, callback_data=f"cancel_preorder:{order.id}")
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="cat_preorder_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def menu_keyboard(items: list) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=f"{item.title} - {item.price}₽", callback_data=f"preorder_item:{item.id}")] for item in items]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="cat_preorder_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def date_keyboard_preorder() -> InlineKeyboardMarkup:
    buttons = []
    today = datetime.date.today()
    days = {"Сегодня": 0, "Завтра": 1, "Послезавтра": 2}
    for text, offset in days.items():
        day = today + datetime.timedelta(days=offset)
        date_iso = day.isoformat()
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"preorder_date:{date_iso}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="preorder_go_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="preorder_go_back")]
    ])

# --- Основные хендлеры ---

@router.callback_query(F.data == "cat_preorder")
async def preorder_menu(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await clear_tracked_messages(state, bot, callback.from_user.id)
    sent_message = await callback.message.answer("Выберите действие:", reply_markup=preorder_main_kb())
    await track_message(state, sent_message)
    await callback.answer()

@router.callback_query(F.data == "cat_preorder_menu")
async def preorder_menu_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    edited_message = await callback.message.edit_text("Выберите действие:", reply_markup=preorder_main_kb())
    await track_message(state, edited_message)
    await callback.answer()

# --- Универсальный хендлер "Назад" ---
@router.callback_query(F.data == "preorder_go_back", StateFilter(PreorderFSM))
async def preorder_go_back_handler(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    edited_message = None

    if current_state == PreorderFSM.entering_quantity:
        edited_message = await callback.message.edit_text(
            "Введите желаемое время готовности заказа в формате <b>ЧЧ:ММ</b> (например, 19:30):",
            reply_markup=back_kb()
        )
        await state.set_state(PreorderFSM.choosing_time)
    elif current_state == PreorderFSM.choosing_time:
        edited_message = await callback.message.edit_text("Выберите дату:", reply_markup=date_keyboard_preorder())
        await state.set_state(PreorderFSM.choosing_date)
    elif current_state == PreorderFSM.choosing_date:
        items = await get_menu_items()
        edited_message = await callback.message.edit_text("Выберите блюдо для предзаказа:", reply_markup=menu_keyboard(items))
        await state.set_state(PreorderFSM.choosing_item)
    
    if edited_message:
        await track_message(state, edited_message)
    await callback.answer()

# --- Сценарий создания предзаказа ---

@router.callback_query(F.data == "create_preorder")
async def create_preorder_start(callback: CallbackQuery, state: FSMContext):
    items = await get_menu_items()
    if not items:
        await callback.answer("К сожалению, меню сейчас пустое.", show_alert=True)
        return
    edited_message = await callback.message.edit_text("Выберите блюдо для предзаказа:", reply_markup=menu_keyboard(items))
    await track_message(state, edited_message)
    await state.set_state(PreorderFSM.choosing_item)
    await callback.answer()

@router.callback_query(F.data.startswith("preorder_item:"), PreorderFSM.choosing_item)
async def item_chosen(callback: CallbackQuery, state: FSMContext):
    await state.update_data(item_id=int(callback.data.split(":")[1]))
    edited_message = await callback.message.edit_text("Выберите дату:", reply_markup=date_keyboard_preorder())
    await track_message(state, edited_message)
    await state.set_state(PreorderFSM.choosing_date)
    await callback.answer()

@router.callback_query(F.data.startswith("preorder_date:"), PreorderFSM.choosing_date)
async def date_chosen_preorder(callback: CallbackQuery, state: FSMContext):
    await state.update_data(date=callback.data.split(":")[1])
    edited_message = await callback.message.edit_text(
        "Введите желаемое время готовности заказа в формате <b>ЧЧ:ММ</b> (например, 19:30):",
        reply_markup=back_kb()
    )
    await track_message(state, edited_message)
    await state.set_state(PreorderFSM.choosing_time)
    await callback.answer()

@router.message(PreorderFSM.choosing_time, F.text)
async def time_entered(message: Message, state: FSMContext, bot: Bot):
    user_time = message.text.strip()
    try:
        datetime.datetime.strptime(user_time, "%H:%M")
    except ValueError:
        await message.delete()
        # Сообщение об ошибке временное, его не нужно отслеживать
        await message.answer("❗️ <b>Неверный формат времени.</b>\nВведите время в формате <b>ЧЧ:ММ</b> (например, 14:00).")
        return
        
    await state.update_data(time=user_time)
    await clear_tracked_messages(state, bot, message.from_user.id)
    await message.delete()
    
    sent_message = await message.answer(
        "Введите количество порций:",
        reply_markup=back_kb()
    )
    await track_message(state, sent_message)
    await state.set_state(PreorderFSM.entering_quantity)

@router.message(PreorderFSM.entering_quantity, F.text)
async def quantity_entered(message: Message, state: FSMContext, bot: Bot):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.delete()
        await message.answer("Пожалуйста, введите корректное число (например: 1).")
        return
        
    quantity = int(message.text)
    await clear_tracked_messages(state, bot, message.from_user.id)
    await message.delete()
    data = await state.get_data()
    await create_preorder(
        tg_id=message.from_user.id,
        item_id=data['item_id'],
        quantity=quantity,
        ready_date=data['date'],
        ready_time=data['time']
    )
    item = await get_menu_item_by_id(data['item_id'])
    item_title = item.title if item else "Выбранное блюдо"
    await message.answer(
        f"✅ Ваш предзаказ сохранён!\n\n"
        f"— Блюдо: {item_title}\n"
        f"— Количество: {quantity} шт.\n"
        f"— Дата и время готовности: <b>{data['date']} {data['time']}</b>"
    )
    await state.clear()

# --- Сценарий просмотра и отмены предзаказов ---
@router.callback_query(F.data == "user_preorders")
async def show_my_preorders(callback: CallbackQuery, state: FSMContext):
    preorders = await get_user_preorders(callback.from_user.id)
    if not preorders:
        await callback.answer("У вас пока нет активных предзаказов.", show_alert=True)
        return
    edited_message = await callback.message.edit_text(
        "Нажмите на предзаказ, чтобы отменить его:",
        reply_markup=preorders_list_keyboard(preorders)
    )
    await track_message(state, edited_message)
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_preorder:"))
async def confirm_cancel_preorder(callback: CallbackQuery, state: FSMContext):
    await state.update_data(cancel_preorder_id=int(callback.data.split(":")[1]))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да, отменить", callback_data="confirm_cancel_preorder"),
            InlineKeyboardButton(text="Нет, оставить", callback_data="deny_cancel_preorder")
        ]
    ])
    await callback.message.edit_text("Вы уверены, что хотите отменить этот предзаказ?", reply_markup=kb)
    await state.set_state(PreorderFSM.confirming_cancel)
    await callback.answer()

@router.callback_query(F.data == "confirm_cancel_preorder", PreorderFSM.confirming_cancel)
async def do_cancel_preorder(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    preorder_id = data.get('cancel_preorder_id')
    await cancel_preorder(preorder_id)
    await state.clear()
    await callback.answer("Предзаказ отменен!", show_alert=True)
    await show_my_preorders(callback, state)

@router.callback_query(F.data == "deny_cancel_preorder", PreorderFSM.confirming_cancel)
async def deny_cancel_preorder(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_my_preorders(callback, state)