import re
from langchain.tools import tool
from ..database import SessionLocal
from typing import Union
from pydantic import BaseModel, Field
from ..schemas import MultiOrder
from ..services import OrderService, ProductService
# from ..config import config
from ..context import current_user_id


def get_user_id() -> int | None:

    return current_user_id.get()

class PizzaPriceInput(BaseModel):
    name: str = Field(
        description="Название пиццы для поиска цены"
    )

@tool(
    description="Сохранение заказа в базу данных",
    args_schema=MultiOrder,
)
def save_order(
    items,
    address: str,
    status: str = "новый",
) -> str:
    """
    Сохраняет заказ с несколькими пиццами в базу данных.

    Вызывается ТОЛЬКО после подтверждения пользователя
    (перехватывается HITLManager.wrap_tool_call).
    """

    order_data = MultiOrder(
        items=items,
        address=address,
        status=status,
    )

    with SessionLocal() as session:
        service = OrderService(session)

        user_id = get_user_id()
        if user_id is None:
            raise ValueError("ID пользователя не найден")

        order = service.create_order(
            user_id=user_id,
            items=order_data.items,
            address=order_data.address,
            status=order_data.status,      # ← не "новый" хардкодом
        )

        return f"Заказ #{order.id} успешно сохранён!"


@tool
def get_pizza_names() -> str:
    """
    Выдача названий пицц, доступных для заказа.
    """

    try:
        with SessionLocal() as session:
            service = ProductService(session)

            products = service.get_all_products()

            if not products:
                return "В меню нет пицц"

            names = [product.name for product in products]

            return "Доступные пиццы: " + ", ".join(names)

    except Exception as e:
        return f"Ошибка при получении списка: {e}"


@tool(args_schema=PizzaPriceInput)
def get_pizza_price(name: str) -> Union[int, str]:
    """
    Выдача цены пиццы по названию.
    """

    try:
        with SessionLocal() as session:
            service = ProductService(session)

            product = service.get_product(name)

            if product:
                return int(product.price)

            return (
                "Пицца с указанным названием отсутствует "
                "в перечне. Уточни название у пользователя."
            )

    except Exception as e:
        return f"Ошибка при поиске цены: {e}"

@tool(description="Проверяет адрес доставки перед оформлением заказа")
def verify_address_before_order(address: str) -> str:
    """
    Проверяет, что адрес доставки указан и содержит номер дома.
    """

    if not address or not address.strip():
        return "Для оформления заказа необходим адрес доставки."

    if not re.search(r"\d+", address):
        return "В адресе не указан номер дома."

    if len(address.strip()) < 5:
        return "Адрес слишком короткий."

    return f"Адрес доставки проверен: {address}"

