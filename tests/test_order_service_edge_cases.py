import pytest
from pydantic import ValidationError
from decimal import Decimal

from modules.database.models import ProductDB, UserDB
from modules.schemas import OrderItem

from modules.services.order import OrderService
from modules.schemas import OrderItem


def test_order_item_rejects_zero_quantity():
    with pytest.raises(ValidationError):
        OrderItem(
            name="Маргарита",
            quantity=0,
        )


def test_order_item_rejects_negative_quantity():
    with pytest.raises(ValidationError):
        OrderItem(
            name="Маргарита",
            quantity=-1,
        )


def test_calculate_order_rejects_unknown_product(session):
    service = OrderService(session)

    items = [
        OrderItem(
            name="Несуществующая пицца",
            quantity=1,
        )
    ]

    with pytest.raises(ValueError):
        service.calculate_order(items)

import pytest

from modules.services.order import OrderService


def test_create_order_rejects_empty_items(session):
    service = OrderService(session)

    with pytest.raises(ValueError):
        service.create_order(
            user_id="1",
            items=[],
            address="Победа 22",
            status="новый",
        )

def test_create_order_creates_user_if_not_exists(session):
    service = OrderService(session)

    product = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    session.add(product)
    session.commit()

    items = [
        OrderItem(
            name="Маргарита",
            quantity=1,
        )
    ]

    order = service.create_order(
        user_id="999",
        items=items,
        address="Победа 22",
        status="новый",
    )

    user = session.get(UserDB, 999)

    assert order.user_id == 999
    assert user is not None
    assert user.address == "Победа 22"
    assert user.last_order_id == order.id     


def test_create_order_rolls_back_order_when_commit_fails(session, monkeypatch):
    service = OrderService(session)

    product = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    user = UserDB(
        user_id=1,
        user_name="Алексей",
        address=None,
        last_order_id=None,
        last_orders=[],
    )

    session.add_all([product, user])
    session.commit()

    original_commit = session.commit

    def broken_commit():
        raise RuntimeError("Ошибка commit")

    monkeypatch.setattr(
        session,
        "commit",
        broken_commit,
    )

    items = [
        OrderItem(
            name="Маргарита",
            quantity=1,
        )
    ]

    with pytest.raises(RuntimeError, match="Ошибка commit"):
        service.create_order(
            user_id="1",
            items=items,
            address="Победа 22",
            status="новый",
        )

    monkeypatch.setattr(
        session,
        "commit",
        original_commit,
    )

    session.rollback()

    order = service.order_repository.get_by_id(1)

    user = session.get(UserDB, 1)

    assert order is None
    assert user.address is None
    assert user.last_order_id is None
    assert user.last_orders == []


def test_create_order_rolls_back_when_user_update_fails(
    session,
    monkeypatch,
):
    service = OrderService(session)

    product = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    user = UserDB(
        user_id=1,
        user_name="Алексей",
        address=None,
        last_order_id=None,
        last_orders=[],
    )

    session.add_all([product, user])
    session.commit()

    def broken_update(*args, **kwargs):
        raise RuntimeError("Ошибка обновления пользователя")

    monkeypatch.setattr(
        service.user_repository,
        "update_last_orders",
        broken_update,
    )

    items = [
        OrderItem(
            name="Маргарита",
            quantity=1,
        )
    ]

    with pytest.raises(
        RuntimeError,
        match="Ошибка обновления пользователя",
    ):
        service.create_order(
            user_id="1",
            items=items,
            address="Победа 22",
            status="новый",
        )

    session.rollback()

    order = service.order_repository.get_by_id(1)
    user = session.get(UserDB, 1)

    assert order is None

    assert user.address is None
    assert user.last_order_id is None
    assert user.last_orders == []    