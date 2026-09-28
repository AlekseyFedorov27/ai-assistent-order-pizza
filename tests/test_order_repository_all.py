from decimal import Decimal

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
        address=f"Адрес {order_id}",
        total=Decimal("339.00"),
        status="новый",
    )

    session.add(order)
    session.commit()

    return order


def test_get_all_returns_all_orders(session):
    """
    get_all должен вернуть заказы всех пользователей.
    """

    create_order(session, 1, 10)
    create_order(session, 2, 20)
    create_order(session, 3, 30)

    repository = OrderRepository(session)

    orders = repository.get_all()

    assert len(orders) == 3
    assert {order.id for order in orders} == {1, 2, 3}


def test_get_all_respects_limit(session):
    """
    get_all должен ограничивать количество возвращаемых заказов.
    """

    create_order(session, 1, 10)
    create_order(session, 2, 20)
    create_order(session, 3, 30)
    create_order(session, 4, 40)
    create_order(session, 5, 50)

    repository = OrderRepository(session)

    orders = repository.get_all(limit=3)

    assert len(orders) == 3


def test_get_all_returns_empty_list_when_no_orders(session):
    """
    Если заказов нет, get_all должен вернуть пустой список.
    """

    repository = OrderRepository(session)

    orders = repository.get_all()

    assert orders == []


def test_get_all_returns_orders_from_different_users(session):
    """
    get_all должен возвращать заказы независимо от user_id.
    """

    create_order(session, 1, 10)
    create_order(session, 2, 10)
    create_order(session, 3, 20)

    repository = OrderRepository(session)

    orders = repository.get_all()

    user_ids = {
        order.user_id
        for order in orders
    }

    assert user_ids == {10, 20}