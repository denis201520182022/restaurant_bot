from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# Reply-клавиатура (фиксированная, всегда под полем ввода)
def main_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Опции")],
            [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )

# Inline-клавиатура (для приветственного сообщения и кнопки «Опции»)
def options_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Меню", callback_data="cat_menu")],
        [InlineKeyboardButton(text="Бронь столиков", callback_data="cat_booking")],
        [InlineKeyboardButton(text="Предзаказ", callback_data="cat_preorder")],
        [InlineKeyboardButton(text="Справка", callback_data="cat_help")],
    ])
