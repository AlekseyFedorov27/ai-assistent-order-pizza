from langchain.tools import tool
from ..database import SessionLocal
from ..services import UserService
# from ..config import config
from ..context import current_user_id

# def get_user_id() -> int | None:

#     user_id = (
#         config
#         .get("configurable", {})
#         .get("user_id")
#     )

#     if user_id is None:
#         return None

#     return int(user_id)

def get_user_id() -> int | None:

    return current_user_id.get()

@tool(
    description="Получить сохранённый адрес пользователя",
)
def get_user_address() -> str:
    """
    Возвращает сохранённый адрес пользователя.
    """

    user_id = get_user_id()

    if user_id is None:
        return "Не удалось определить пользователя."

    try:
        with SessionLocal() as session:

            service = UserService(session)

            user = service.get_user_data(user_id)

            if user is None or not user.address:
                return (
                    "У вас нет сохранённого адреса. "
                    "Пожалуйста, укажите адрес для доставки."
                )

            return (
                f"Адрес пользователя: {user.address}"
            )

    except Exception as e:
        return f"Ошибка при получении адреса: {e}"


@tool(
    description="Возвращает статус последнего заказа пользователя",
)
def get_status_last_order() -> str:
    """
    Возвращает статус последнего заказа текущего пользователя.
    """

    user_id = get_user_id()

    if user_id is None:
        return "Не удалось определить пользователя."

    try:
        with SessionLocal() as session:

            service = UserService(session)

            user = service.get_user_data(user_id)

            if user is None:
                return "Пользователь не найден."

            if user.last_order_id is None:
                return "У пользователя нет заказов."

            status = service.get_status(
                user.last_order_id
            )

            return (
                f"Статус последнего заказа: {status}"
            )

    except Exception as e:
        return f"Ошибка при получении статуса: {e}"


@tool(
    description="Получить историю десяти последних заказов пользователя",
)
def get_user_last_orders() -> str:
    """
    Возвращает десять последних заказов пользователя.
    """

    user_id = get_user_id()

    if user_id is None:
        return "Не удалось определить пользователя."

    try:
        with SessionLocal() as session:

            service = UserService(session)

            orders = service.get_user_orders(
                user_id=user_id,
                limit=10,
            )

            if not orders:
                return "У вас нет истории заказов."

            return "Последние заказы:\n" + "\n".join(
                f"Заказ #{order.id}:\n"
                + "\n".join(
                    f"  {item.name} {item.quantity} шт. по {item.price} руб."
                    for item in order.items
                )
                + f"\n  Общая цена заказа: {order.total} руб. Дата {order.created_at.strftime("%d.%m.%Y %H:%M")}"
                for order in orders
            )

    except Exception as e:
        return (
            f"Ошибка при получении истории заказов: {e}"
        )


@tool(
    description="Сохранить адрес пользователя",
)
def save_user_address(
    address: str,
) -> str:
    """
    Сохраняет адрес пользователя.
    """

    user_id = get_user_id()

    if user_id is None:
        return "Не удалось определить пользователя."

    try:
        with SessionLocal() as session:

            service = UserService(session)

            saved_address = service.update_address(
                user_id=user_id,
                address=address,
            )

            return (
                f"Адрес сохранён: {saved_address}"
            )

    except Exception as e:
        return (
            f"Ошибка сохранения адреса: {e}"
        )