from pydantic import BaseModel, Field
from .order import OrderItem


class User(BaseModel):
    user_id: int

    user_name: str | None = Field(
        default=None,
        description="Имя пользователя",
    )

    address: str | None = Field(
        default=None,
        description="Адрес пользователя",
    )

    last_orders: list[OrderItem] = Field(
        default_factory=list,
        description="Последние заказы пользователя",
    )

    last_order_id: int | None = Field(
        default=None,
        description="ID последнего заказа пользователя",
    )