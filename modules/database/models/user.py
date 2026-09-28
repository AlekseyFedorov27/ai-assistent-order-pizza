from typing import Any
from sqlalchemy import Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from ..base import Base


class UserDB(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    last_orders: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    last_order_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "orders.id",
            use_alter=True,
        ),
        nullable=True,
    )