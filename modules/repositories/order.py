from decimal import Decimal
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database.models import OrderDB


class OrderRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        user_id: int,
        items: list[dict[str, Any]],
        address: str,
        total: Decimal,
        status: str,
    ) -> OrderDB:

        order = OrderDB(
            user_id=user_id,
            items=items,
            address=address,
            total=total,
            status=status,
        )

        self.session.add(order)
        self.session.flush()

        return order


    def get_by_id(
        self,
        order_id: int,
    ) -> OrderDB | None:

        stmt = select(OrderDB).where(
            OrderDB.id == order_id
        )

        return self.session.scalar(stmt)

    def get_user_orders(
        self,
        user_id: int,
    ) -> list[OrderDB]:

        stmt = (
            select(OrderDB)
            .where(OrderDB.user_id == user_id)
            .order_by(OrderDB.created_at.desc())
        )

        return list(
            self.session.scalars(stmt).all()
        )

    def get_all(
        self,
        limit: int = 100,
    ) -> list[OrderDB]:

        stmt = (
            select(OrderDB)
            .order_by(OrderDB.created_at.desc())
            .limit(limit)
        )

        return list(
            self.session.scalars(stmt).all()
        )