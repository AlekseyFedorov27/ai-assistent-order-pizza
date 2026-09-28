from decimal import Decimal
from datetime import datetime

import pytest

from modules.database.models import UserDB, OrderDB
from modules.services.user import UserService


def create_user(session, user_id=1):
    user = UserDB(
        user_id=user_id,
        user_name="Алексей",
        address="Победа 22",
        last_order_id=None,
        last_orders=[],
    )

    session.add(user)
    session.commit()

    return user


def create_order(
    session,
    user_id,
    total="678.00",
    status="новый",
):
    order = OrderDB(
        user_id=user_id,
        items=[
            {
                "name": "Маргарита",
                "price": "339.00",
                "quantity": 2,
                "subtotal": "678.00",
            }
        ],
        address="Победа 22",
        total=Decimal(total),
        status=status,
    )

    session.add(order)
    session.commit()

    return order


def test_get_user_orders_returns_orders(session):
    """
    UserService должен возвращать заказы пользователя.
    """

    create_user(session, user_id=1)
    order = create_order(session, user_id=1)

    service = UserService(session)

    result = service.get_user_orders(user_id=1)

    assert len(result) == 1

    assert result[0].id == order.id
    assert result[0].user_id == 1
    assert result[0].address == "Победа 22"
    assert result[0].total == Decimal("678.00")
    assert result[0].status == "новый"


def test_get_user_orders_returns_empty_list(session):
    """
    Если у пользователя нет заказов,
    сервис должен вернуть пустой список.
    """

    create_user(session, user_id=1)

    service = UserService(session)

    result = service.get_user_orders(user_id=1)

    assert result == []


def test_get_user_orders_respects_limit(session):
    """
    limit должен ограничивать количество возвращаемых заказов.
    """

    create_user(session, user_id=1)

    for _ in range(5):
        create_order(session, user_id=1)

    service = UserService(session)

    result = service.get_user_orders(
        user_id=1,
        limit=3,
    )

    assert len(result) == 3


def test_get_user_orders_limit_must_be_positive(session):
    """
    limit <= 0 должен вызывать ValueError.
    """

    service = UserService(session)

    with pytest.raises(
        ValueError,
        match="limit должен быть больше 0",
    ):
        service.get_user_orders(
            user_id=1,
            limit=0,
        )


def test_get_user_orders_negative_limit(session):
    """
    Отрицательный limit также должен вызывать ValueError.
    """

    service = UserService(session)

    with pytest.raises(
        ValueError,
        match="limit должен быть больше 0",
    ):
        service.get_user_orders(
            user_id=1,
            limit=-1,
        )


def test_get_user_orders_does_not_return_other_users_orders(session):
    """
    Заказы другого пользователя не должны попадать
    в историю текущего пользователя.
    """

    create_user(session, user_id=1)
    create_user(session, user_id=2)

    order_user_1 = create_order(
        session,
        user_id=1,
    )

    create_order(
        session,
        user_id=2,
    )

    service = UserService(session)

    result = service.get_user_orders(
        user_id=1,
    )

    assert len(result) == 1
    assert result[0].id == order_user_1.id
    assert result[0].user_id == 1
    

def test_get_all_orders_returns_all_orders(session):
    """
    get_all_orders должен возвращать заказы всех пользователей.
    """

    create_user(session, user_id=1)
    create_user(session, user_id=2)

    order_1 = create_order(session, user_id=1)
    order_2 = create_order(
        session,
        user_id=2,
        total="1017.00",
    )

    service = UserService(session)

    result = service.get_all_orders()

    assert len(result) == 2

    order_ids = {order.id for order in result}

    assert order_1.id in order_ids
    assert order_2.id in order_ids


def test_get_all_orders_respects_limit(session):
    """
    limit должен ограничивать количество всех заказов.
    """

    create_user(session, user_id=1)

    for _ in range(5):
        create_order(session, user_id=1)

    service = UserService(session)

    result = service.get_all_orders(limit=3)

    assert len(result) == 3


def test_get_all_orders_limit_must_be_positive(session):
    """
    limit <= 0 должен вызывать ValueError.
    """

    service = UserService(session)

    with pytest.raises(
        ValueError,
        match="limit должен быть больше 0",
    ):
        service.get_all_orders(limit=0)


def test_get_status_returns_order_status(session):
    """
    get_status должен возвращать статус существующего заказа.
    """

    create_user(session, user_id=1)

    order = create_order(
        session,
        user_id=1,
        status="новый",
    )

    service = UserService(session)

    result = service.get_status(order.id)

    assert result == "новый"


def test_get_status_returns_not_found_for_unknown_order(session):
    """
    Для несуществующего заказа должен возвращаться
    текст 'заказ не найден'.
    """

    service = UserService(session)

    result = service.get_status(999)

    assert result == "заказ не найден"