from decimal import Decimal

from modules.database.models import OrderDB
from modules.repositories.order import OrderRepository


def create_order(
    session,
    order_id: int,
    user_id: int,
    address: str = "Победа 22",
    total: str = "678.00",
):
    order = OrderDB(
        id=order_id,
        user_id=user_id,
        items=[
            {
                "name": "Маргарита",
                "price": "339.00",
                "quantity": 2,
                "subtotal": "678.00",
            }
        ],
        address=address,
        total=Decimal(total),
        status="новый",
    )

    session.add(order)
    session.commit()

    return order


def test_get_by_id_returns_order(session):
    """
    get_by_id должен вернуть существующий заказ.
    """

    create_order(
        session=session,
        order_id=1,
        user_id=10,
    )

    repository = OrderRepository(session)

    order = repository.get_by_id(1)

    assert order is not None
    assert order.id == 1
    assert order.user_id == 10
    assert order.address == "Победа 22"
    assert order.total == Decimal("678.00")


def test_get_by_id_returns_none_for_unknown_order(session):
    """
    Если заказа нет, get_by_id должен вернуть None.
    """

    repository = OrderRepository(session)

    order = repository.get_by_id(999)

    assert order is None


def test_get_user_orders_returns_only_user_orders(session):
    """
    Пользователь должен получать только свои заказы.
    """

    create_order(
        session=session,
        order_id=1,
        user_id=10,
    )

    create_order(
        session=session,
        order_id=2,
        user_id=20,
    )

    create_order(
        session=session,
        order_id=3,
        user_id=10,
    )

    repository = OrderRepository(session)

    orders = repository.get_user_orders(
        user_id=10,
    )

    assert len(orders) == 2

    assert all(
        order.user_id == 10
        for order in orders
    )

    assert {order.id for order in orders} == {1, 3}


def test_get_user_orders_returns_empty_list(session):
    """
    Если у пользователя нет заказов,
    должен вернуться пустой список.
    """

    repository = OrderRepository(session)

    orders = repository.get_user_orders(
        user_id=999,
    )

    assert orders == []