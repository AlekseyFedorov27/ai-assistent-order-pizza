from decimal import Decimal

from modules.database import Base
from modules.database.models import UserDB
from modules.repositories.user import UserRepository


def test_get_or_create_creates_user(session):
    repository = UserRepository(session)

    user = repository.get_or_create(user_id=1)

    assert user.user_id == 1
    assert user.address is None
    assert user.last_order_id is None
    assert user.last_orders == []


def test_get_or_create_returns_existing_user(session):
    user = UserDB(
        user_id=1,
        address="Победа 22",
        last_order_id=5,
        last_orders=[],
    )

    session.add(user)
    session.commit()

    repository = UserRepository(session)

    result = repository.get_or_create(user_id=1)

    assert result.user_id == 1
    assert result.address == "Победа 22"
    assert result.last_order_id == 5

def test_get_user_by_id(session):
    user = UserDB(
        user_id=1,
        user_name="Алексей",
    )

    session.add(user)
    session.commit()

    repository = UserRepository(session)

    result = repository.get_by_id(1)

    assert result is not None
    assert result.user_id == 1
    assert result.user_name == "Алексей"


def test_get_user_by_id_returns_none_for_unknown_user(session):
    repository = UserRepository(session)

    result = repository.get_by_id(999)

    assert result is None


def test_update_address(session):
    user = UserDB(
        user_id=1,
        user_name="Алексей",
        address="Лугова 45",
    )

    session.add(user)
    session.commit()

    repository = UserRepository(session)

    repository.update_address(
        user_id=1,
        address="Победа 22",
    )

    session.commit()

    updated_user = repository.get_by_id(1)

    assert updated_user.address == "Победа 22"


def test_update_last_order_id(session):
    user = UserDB(
        user_id=1,
        user_name="Алексей",
        last_order_id=None,
    )

    session.add(user)
    session.commit()

    repository = UserRepository(session)

    repository.update_last_order_id(
        user_id=1,
        order_id=5,
    )

    session.commit()

    updated_user = repository.get_by_id(1)

    assert updated_user.last_order_id == 5


def test_update_last_orders(session):
    user = UserDB(
        user_id=1,
        user_name="Алексей",
    )

    session.add(user)
    session.commit()

    repository = UserRepository(session)

    order = {
        "order_id": 1,
        "items": [
            {
                "name": "Маргарита",
                "price": "339.00",
                "quantity": 2,
                "subtotal": "678.00",
            }
        ],
        "address": "Победа 22",
        "total": "678.00",
        "status": "новый",
    }

    repository.update_last_orders(
        user_id=1,
        last_order=order,
    )

    session.commit()

    result = repository.get_by_id(1)

    assert result.last_orders == [order]


def test_update_last_orders_keeps_only_last_10(session):
    user = UserDB(
        user_id=1,
        user_name="Алексей",
        last_orders=[],
    )

    session.add(user)
    session.commit()

    repository = UserRepository(session)

    for order_id in range(1, 13):
        repository.update_last_orders(
            user_id=1,
            last_order={
                "order_id": order_id,
                "items": [],
                "address": "Победа 22",
                "total": "100.00",
                "status": "новый",
            },
        )

    session.commit()

    result = repository.get_by_id(1)

    assert len(result.last_orders) == 10
    assert result.last_orders[0]["order_id"] == 3
    assert result.last_orders[-1]["order_id"] == 12