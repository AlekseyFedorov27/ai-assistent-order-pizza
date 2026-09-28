from typing import Any
from sqlalchemy.orm import Session
from ..database.models import UserDB


class UserRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_or_create(
        self,
        user_id: int,
    ) -> UserDB:

        user = self.session.get(UserDB, user_id)

        if user is None:
            user = UserDB(
                user_id=user_id,
                address=None,
                last_order_id=None,
                last_orders=[],
            )

            self.session.add(user)
            self.session.flush()

        return user

    def get_by_id(
        self,
        user_id: int,
    ) -> UserDB | None:

        return self.session.get(UserDB, user_id)

    def update_last_order_id(
        self,
        user_id: int,
        order_id: int,
    ) -> None:

        user = self.get_or_create(user_id)
        user.last_order_id = order_id

    def update_address(
        self,
        user_id: int,
        address: str,
    ) -> None:

        user = self.get_or_create(user_id)
        user.address = address

    def update_last_orders(
        self,
        user_id: int,
        last_order: dict[str, Any],
    ) -> None:

        user = self.get_or_create(user_id)

        current_orders = user.last_orders or []

        user.last_orders = (
            current_orders + [last_order]
        )[-10:]