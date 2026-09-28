from sqlalchemy.orm import Session
from ..repositories.order import OrderRepository
from ..repositories.user import UserRepository
from ..database.models import UserDB
from ..schemas import OrderResponse


class UserService:

    def __init__(
        self,
        session: Session,
        store=None,
    ):
        self.session = session
        self.user_repository = UserRepository(session)
        self.order_repository = OrderRepository(session)
        self.store = store


    def load_user_to_store(
        self,
        user_id: int,
    ) -> UserDB | None:

        if self.store is None:
            raise ValueError(
                "Store не передан в UserService"
            )

        user = self.user_repository.get_by_id(user_id)

        if user is None:
            return None

        self.store.put(
            ("users",),
            str(user_id),
            {
                "user_id": user.user_id,
                "address": user.address,
                "last_order_id": user.last_order_id,
                "last_orders": user.last_orders,
            },
        )

        return user

    def get_user_data(
        self,
        user_id: int,
    ) -> UserDB | None:

        user = self.user_repository.get_by_id(user_id)

        if user is None:
            return None

        return user

    def get_user_orders(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[OrderResponse]:

        if limit <= 0:
            raise ValueError(
                "limit должен быть больше 0"
            )

        orders = self.order_repository.get_user_orders(
            user_id=user_id,
        )

        orders = orders[:limit]

        return [
            self._to_schema(order)
            for order in orders
        ]

    def get_all_orders(
        self,
        limit: int = 100,
    ) -> list[OrderResponse]:

        if limit <= 0:
            raise ValueError(
                "limit должен быть больше 0"
            )

        orders = self.order_repository.get_all(limit)

        return [
            self._to_schema(order)
            for order in orders
        ]

    def update_address(
        self,
        *,
        user_id: int,
        address: str,
    ) -> str:

        try:
            self.user_repository.update_address(
                user_id=user_id,
                address=address,
            )

            self.session.commit()

            return address

        except Exception:
            self.session.rollback()
            raise

    def update_last_order_id(
        self,
        *,
        user_id: int,
        order_id: int,
    ) -> None:

        try:
            self.user_repository.update_last_order_id(
                user_id=user_id,
                order_id=order_id,
            )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

    def get_status(
        self,
        order_id: int,
    ) -> str:

        order = self.order_repository.get_by_id(order_id)

        if order is None:
            return "заказ не найден"

        return order.status

    @staticmethod
    def _to_schema(
        order,
    ) -> OrderResponse:

        return OrderResponse.model_validate(
            order,
            from_attributes=True,
        )