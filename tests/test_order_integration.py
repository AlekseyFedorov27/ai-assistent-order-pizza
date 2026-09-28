from decimal import Decimal

import pytest

from decimal import Decimal

from modules.database.models import (
    UserDB,
    ProductDB,
    OrderDB,
)

from modules.schemas import OrderItem
from modules.services.order import OrderService

from modules.database.models import ProductDB, UserDB
from modules.schemas import OrderItem, Product
from modules.services.order import OrderService


def test_create_order_full_integration(session):
    """
    Полный интеграционный тест создания заказа.

    Проверяем реальную цепочку:

    ProductDB
        ↓
    ProductRepository
        ↓
    OrderService
        ↓
    OrderRepository
        ↓
    UserRepository
        ↓
    SQLite
    """

    # Создаём пользователя
    user = UserDB(
        user_id=1,
        user_name="Алексей",
        address=None,
        last_order_id=None,
        last_orders=[],
    )

    session.add(user)

    # Создаём товар
    product = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    session.add(product)
    session.commit()

    # Создаём сервис
    service = OrderService(session)

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        )
    ]

    # Создаём заказ
    order = service.create_order(
        user_id="1",
        items=items,
        address="Победа 22",
        status="новый",
    )

    # Проверяем сам заказ
    assert order.id is not None
    assert order.user_id == 1
    assert order.address == "Победа 22"
    assert order.total == Decimal("678.00")
    assert order.status == "новый"

    # Проверяем позиции заказа
    assert order.items == [
        {
            "name": "Маргарита",
            "price": "339.00",
            "quantity": 2,
            "subtotal": "678.00",
        }
    ]

    # Проверяем пользователя после создания заказа
    session.refresh(user)

    assert user.last_order_id == order.id
    assert user.address == "Победа 22"

    # Проверяем историю заказов
    assert len(user.last_orders) == 1

    last_order = user.last_orders[0]

    assert last_order["order_id"] == order.id
    assert last_order["address"] == "Победа 22"
    assert last_order["total"] == "678.00"
    assert last_order["status"] == "новый"

    assert last_order["items"] == [
        {
            "name": "Маргарита",
            "price": "339.00",
            "quantity": 2,
            "subtotal": "678.00",
        }
    ]


def test_create_order_updates_user_data(session):
    """
    После создания заказа у пользователя должны обновиться:

    - last_order_id
    - address
    - last_orders
    """

    user = UserDB(
        user_id=1,
        user_name="Алексей",
        address=None,
        last_order_id=None,
        last_orders=[],
    )

    product = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    session.add_all([user, product])
    session.commit()

    service = OrderService(session)

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        )
    ]

    order = service.create_order(
        user_id="1",
        items=items,
        address="Победа 22",
        status="новый",
    )

    # Получаем пользователя заново из БД
    session.expire_all()

    saved_user = session.get(UserDB, 1)

    assert saved_user is not None

    # last_order_id должен указывать на созданный заказ
    assert saved_user.last_order_id == order.id

    # Адрес должен сохраниться
    assert saved_user.address == "Победа 22"

    # Должна сохраниться история заказа
    assert len(saved_user.last_orders) == 1

    last_order = saved_user.last_orders[0]

    assert last_order["order_id"] == order.id
    assert last_order["address"] == "Победа 22"
    assert last_order["total"] == "678.00"
    assert last_order["status"] == "новый"

    # Проверяем товары внутри истории
    assert last_order["items"] == [
        {
            "name": "Маргарита",
            "price": "339.00",
            "quantity": 2,
            "subtotal": "678.00",
        }
    ]

def test_create_order_with_multiple_pizzas(session):
    """
    Проверяем создание заказа с несколькими пиццами.

    Проверяем:
    - реальные цены из ProductDB;
    - количество каждой пиццы;
    - subtotal;
    - общий total;
    - сохранение items в JSON.
    """

    user = UserDB(
        user_id=1,
        user_name="Алексей",
        address=None,
        last_order_id=None,
        last_orders=[],
    )

    margarita = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    pesto = ProductDB(
        name="Песта",
        price=Decimal("389.00"),
        category="Пицца",
    )

    session.add_all([
        user,
        margarita,
        pesto,
    ])

    session.commit()

    service = OrderService(session)

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        ),
        OrderItem(
            name="Песта",
            quantity=3,
        ),
    ]

    order = service.create_order(
        user_id="1",
        items=items,
        address="Победа 22",
        status="новый",
    )

    assert order.total == Decimal("1845.00")

    assert order.items == [
        {
            "name": "Маргарита",
            "price": "339.00",
            "quantity": 2,
            "subtotal": "678.00",
        },
        {
            "name": "Песта",
            "price": "389.00",
            "quantity": 3,
            "subtotal": "1167.00",
        },
    ]

    assert order.address == "Победа 22"
    assert order.status == "новый"


def test_create_order_rolls_back_when_user_update_fails(session, monkeypatch):
    """
    Если обновление пользователя падает,
    создание заказа должно полностью откатиться.
    """

    # Пользователь
    user = UserDB(
        user_id=1,
        user_name="Алексей",
        address=None,
        last_order_id=None,
        last_orders=[],
    )

    # Товар
    product = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    session.add_all([user, product])
    session.commit()

    service = OrderService(session)

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        )
    ]

    def broken_update_address(*args, **kwargs):
        raise RuntimeError("Ошибка обновления адреса")

    monkeypatch.setattr(
        service.user_repository,
        "update_address",
        broken_update_address,
    )

    # Создание заказа должно завершиться ошибкой
    with pytest.raises(RuntimeError, match="Ошибка обновления адреса"):
        service.create_order(
            user_id="1",
            items=items,
            address="Победа 22",
            status="новый",
        )

    # После rollback заказа в БД быть не должно
    orders = session.query(OrderDB).all()

    assert orders == []

    # Данные пользователя тоже не должны измениться
    user = session.get(UserDB, 1)

    assert user.address is None
    assert user.last_order_id is None
    assert user.last_orders == []



def test_create_order_rolls_back_when_last_orders_update_fails(
    session,
    monkeypatch,
):
    """
    Если обновление истории заказов пользователя падает,
    создание заказа должно полностью откатиться.
    """

    user = UserDB(
        user_id=1,
        user_name="Алексей",
        address=None,
        last_order_id=None,
        last_orders=[],
    )

    product = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    session.add_all([user, product])
    session.commit()

    service = OrderService(session)

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        )
    ]

    def broken_update_last_orders(*args, **kwargs):
        raise RuntimeError("Ошибка обновления истории заказов")

    monkeypatch.setattr(
        service.user_repository,
        "update_last_orders",
        broken_update_last_orders,
    )

    with pytest.raises(
        RuntimeError,
        match="Ошибка обновления истории заказов",
    ):
        service.create_order(
            user_id="1",
            items=items,
            address="Победа 22",
            status="новый",
        )

    # Заказ не должен сохраниться
    orders = session.query(OrderDB).all()

    assert orders == []

    # Пользователь не должен быть изменён
    user = session.get(UserDB, 1)

    assert user.address is None
    assert user.last_order_id is None
    assert user.last_orders == []    