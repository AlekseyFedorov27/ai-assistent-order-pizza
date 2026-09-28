from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


from modules.database import Base
from modules.repositories.order import OrderRepository


def create_test_session():
    """
    Создаёт отдельную SQLite in-memory базу
    для теста.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
    )

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
    )

    return SessionLocal()


def test_create_order():
    session = create_test_session()

    try:
        repository = OrderRepository(session)

        order_items = [
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

        order = repository.create(
            user_id=1,
            items=order_items,
            address="Победа 22",
            total=Decimal("1845.00"),
            status="новый",
        )

        assert order.id is not None
        assert order.user_id == 1
        assert order.address == "Победа 22"
        assert order.status == "новый"

        assert order.items == order_items

        assert order.total == Decimal("1845.00")

    finally:
        session.close()


def test_create_order_with_decimal_total():
    """
    Проверяем, что Decimal корректно сохраняется
    в колонку total.
    """

    session = create_test_session()

    try:
        repository = OrderRepository(session)

        order = repository.create(
            user_id=1,
            items=[
                {
                    "name": "Маргарита",
                    "price": "339.00",
                    "quantity": 2,
                    "subtotal": "678.00",
                }
            ],
            address="Луговая 45",
            total=Decimal("678.00"),
            status="новый",
        )

        assert order.total == Decimal("678.00")

    finally:
        session.close()


def test_create_order_items_are_json_serializable():
    """
    Проверяем, что items не содержат Decimal,
    который SQLite JSON не умеет сериализовать.
    """

    session = create_test_session()

    try:
        repository = OrderRepository(session)

        order_items = [
            {
                "name": "Маргарита",
                "price": "339.00",
                "quantity": 2,
                "subtotal": "678.00",
            }
        ]

        order = repository.create(
            user_id=1,
            items=order_items,
            address="Победа 22",
            total=Decimal("678.00"),
            status="новый",
        )

        assert order.items[0]["price"] == "339.00"
        assert order.items[0]["subtotal"] == "678.00"

    finally:
        session.close()

