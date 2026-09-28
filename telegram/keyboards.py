from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def order_confirmation_keyboard():

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data="order:approve",
        ),
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="order:reject",
        ),
    )

    return builder.as_markup()