from decimal import Decimal

import pytest

from modules.database.models import OrderDB
from modules.repositories.order import OrderRepository


def create_order(
    session,
    order_id: int,
    user_id: int,
):
    order = OrderDB(
        id=order_id,
        user_id=user_id,
        items=[
            {
                "name": "Маргарита",
                "price": "339.00",
                "quantity": 1,
                "subtotal": "339.00",
            }
        ],
        address="Победа 22",
        total=Decimal("339.00"),
        status="новый",
    )

    session.add(order)
    session.commit()

    return order


def test_get_all_limit_one(session):
    """
    При limit=1 должен вернуться только один заказ.
    """

    create_order(session, 1, 10)
    create_order(session, 2, 20)
    create_order(session, 3, 30)

    repository = OrderRepository(session)

    orders = repository.get_all(limit=1)

    assert len(orders) == 1


def test_get_user_orders_for_single_user(session):
    """
    get_user_orders должен вернуть все заказы
    конкретного пользователя.
    """

    create_order(session, 1, 10)
    create_order(session, 2, 10)
    create_order(session, 3, 10)

    repository = OrderRepository(session)

    orders = repository.get_user_orders(
        user_id=10,
    )

    assert len(orders) == 3
    assert all(
        order.user_id == 10
        for order in orders
    )


def test_get_user_orders_limit_one(session):
    """
    limit должен ограничивать количество заказов
    конкретного пользователя.
    """

    create_order(session, 1, 10)
    create_order(session, 2, 10)
    create_order(session, 3, 10)

    repository = OrderRepository(session)

    orders = repository.get_user_orders(
        user_id=10,
    )[:1]

    assert len(orders) == 1


def test_get_by_id_does_not_return_other_order(session):
    """
    get_by_id должен вернуть именно заказ
    с указанным ID.
    """

    create_order(session, 1, 10)
    create_order(session, 2, 10)

    repository = OrderRepository(session)

    order = repository.get_by_id(2)

    assert order is not None
    assert order.id == 2
    assert order.id != 1