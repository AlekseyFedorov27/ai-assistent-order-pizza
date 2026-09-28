from aiogram import Router, F
from aiogram.types import CallbackQuery
from modules.agent import resume_agent
from .hitl import (
    get_pending_order,
    delete_pending_order,
)


router = Router()


@router.callback_query(
    F.data == "order:approve"
)
async def approve_order(
    callback: CallbackQuery,
):

    user_id = callback.from_user.id

    pending = get_pending_order(user_id)

    if pending is None:

        await callback.answer(
            "Заказ уже обработан.",
            show_alert=True,
        )

        return

    try:

        response = resume_agent(
            user_id=user_id,
            decision={
                "type": "approve",
            },
        )

        delete_pending_order(user_id)

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        answer = response[
            "messages"
        ][-1].content

        await callback.message.answer(
            answer
        )

        await callback.answer(
            "Заказ подтверждён!"
        )

    except Exception as e:

        print(
            f"Ошибка подтверждения заказа "
            f"user_id={user_id}: {e}"
        )

        await callback.answer(
            "Ошибка при подтверждении заказа.",
            show_alert=True,
        )


@router.callback_query(
    F.data == "order:reject"
)
async def reject_order(
    callback: CallbackQuery,
):

    user_id = callback.from_user.id

    pending = get_pending_order(user_id)

    if pending is None:

        await callback.answer(
            "Заказ уже обработан.",
            show_alert=True,
        )

        return

    try:

        response = resume_agent(
            user_id=user_id,
            decision={
                "type": "reject",
                "message": (
                    "Заказ отклонён пользователем. "
                    "Не сохраняй этот заказ."
                ),
            },
        )

        delete_pending_order(user_id)

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        answer = response[
            "messages"
        ][-1].content

        await callback.message.answer(
            answer
        )

        await callback.answer(
            "Заказ отменён."
        )

    except Exception as e:

        print(
            f"Ошибка отмены заказа "
            f"user_id={user_id}: {e}"
        )

        await callback.answer(
            "Ошибка при отмене заказа.",
            show_alert=True,
        )