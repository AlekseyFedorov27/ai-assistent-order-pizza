from decimal import Decimal
from unittest.mock import Mock

import pytest

from modules.schemas import OrderItem
from modules.services.order import OrderService


def create_service():
    session = Mock()

    service = OrderService(session)

    service.product_repository = Mock()

    return service


def test_calculate_order_single_pizza():
    service = create_service()

    product = Mock()
    product.name = "Маргарита"
    product.price = Decimal("339.00")

    service.product_repository.get_by_name.return_value = product

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        )
    ]

    order_items, total = service.calculate_order(items)

    assert total == Decimal("678.00")

    assert order_items == [
        {
            "name": "Маргарита",
            "price": Decimal("339.00"),
            "quantity": 2,
            "subtotal": Decimal("678.00"),
        }
    ]


def test_calculate_order_multiple_pizzas():
    service = create_service()

    margarita = Mock()
    margarita.name = "Маргарита"
    margarita.price = Decimal("339.00")

    pesto = Mock()
    pesto.name = "Песта"
    pesto.price = Decimal("389.00")

    def get_product(name):
        if name == "Маргарита":
            return margarita

        if name == "Песта":
            return pesto

        return None

    service.product_repository.get_by_name.side_effect = get_product

    items = [
        OrderItem(name="Маргарита", quantity=2),
        OrderItem(name="Песта", quantity=3),
    ]

    order_items, total = service.calculate_order(items)

    assert total == Decimal("1845.00")

    assert order_items[0]["subtotal"] == Decimal("678.00")
    assert order_items[1]["subtotal"] == Decimal("1167.00")


def test_calculate_order_unknown_product():
    service = create_service()

    service.product_repository.get_by_name.return_value = None

    items = [
        OrderItem(
            name="Несуществующая пицца",
            quantity=2,
        )
    ]

    with pytest.raises(
        ValueError,
        match="Пицца 'Несуществующая пицца' не найдена",
    ):
        service.calculate_order(items)


def test_price_is_taken_from_database():
    """
    Пользователь не может самостоятельно установить цену.

    Цена должна браться из ProductRepository.
    """

    service = create_service()

    product = Mock()
    product.name = "Маргарита"
    product.price = Decimal("339.00")

    service.product_repository.get_by_name.return_value = product

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        )
    ]

    order_items, total = service.calculate_order(items)

    assert order_items[0]["price"] == Decimal("339.00")
    assert total == Decimal("678.00")

    # Цена пользователя 100 рублей нигде не участвует.
    assert order_items[0]["price"] != Decimal("100.00")


def test_calculate_order_zero_quantity():
    service = create_service()

    product = Mock()
    product.name = "Маргарита"
    product.price = Decimal("339.00")

    service.product_repository.get_by_name.return_value = product

    with pytest.raises(Exception):
        OrderItem(
            name="Маргарита",
            quantity=0,
        )

