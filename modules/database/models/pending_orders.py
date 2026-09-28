from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from ..base import Base


class PendingOrderDB(Base):
    __tablename__ = "pending_orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    thread_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    tool_call_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # что нужно для сохранения заказа после подтверждения
    items: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="новый",
    )

    # что нужно для карточки подтверждения
    preview: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    # состояние прерывания
    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # runtime_config целиком, чтобы resume_agent мог его достать
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )