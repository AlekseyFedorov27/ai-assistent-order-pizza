# telegram/handlers.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from modules.agent import get_agent_response, resume_agent


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🍕 Привет!\n"
        "Я AI-помощник по заказу пиццы.\n\n"
        "Что хотите заказать?"
    )


@router.message()
async def message_handler(message: Message):
    if not message.text:
        return

    user_id = message.from_user.id

    try:
        response = get_agent_response(message=message.text, user_id=user_id)

        if response.get("__interrupt__"):
            preview = _extract_interrupt_value(response)
            if preview is None:
                await message.answer("Не удалось получить данные заказа.")
                return

            await send_order_confirmation(message=message, order=preview)
            return

        await message.answer(response["messages"][-1].content)

    except Exception as e:
        print(f"Ошибка Telegram user_id={user_id}: {e}")
        await message.answer("Произошла ошибка при обработке запроса.")


@router.callback_query(F.data.startswith("order:"))
async def order_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    approved = callback.data == "order:approve"

    try:
        response = resume_agent(
            user_id=user_id,
            decision={"approved": approved},
        )

        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

        await callback.message.answer(response["messages"][-1].content)

    except Exception as e:
        print(f"Ошибка callback user_id={user_id}: {e}")
        await callback.message.answer("Не удалось обработать подтверждение.")
    finally:
        await callback.answer()


def _extract_interrupt_value(response) -> dict | None:
    """
    LangGraph кладёт прерывание в response["__interrupt__"]
    как кортеж Interrupt-объектов. Достаём payload первого.
    """
    data = response.get("__interrupt__")
    if not data:
        return None
    if isinstance(data, (tuple, list)):
        data = data[0]
    value = getattr(data, "value", None)
    if value is None and isinstance(data, dict):
        value = data.get("value") or data
    return value


async def send_order_confirmation(message: Message, order: dict):
    items = order.get("items", [])
    lines = ["🍕 <b>Проверьте заказ</b>", ""]

    for item in items:
        name = item.get("name", "Неизвестная пицца")
        quantity = item.get("quantity", 0)
        price = item.get("price")
        subtotal = item.get("subtotal")
        if price is not None and subtotal is not None:
            lines.append(f"• {name} — {quantity} шт. × {price} ₽ = {subtotal} ₽")
        else:
            lines.append(f"• {name} — {quantity} шт.")

    total = order.get("total")
    address = order.get("address")

    lines.append("")
    if total is not None:
        lines.append(f"💰 <b>Итого:</b> {total} ₽")
    if address:
        lines.append(f"📍 <b>Адрес:</b> {address}")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="order:approve"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="order:reject"),
        ]]
    )

    await message.answer("\n".join(lines), reply_markup=keyboard, parse_mode="HTML")