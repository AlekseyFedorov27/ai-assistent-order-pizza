import pytest
from pydantic import ValidationError

from modules.schemas import OrderItem, MultiOrder


def test_order_item_valid():
    item = OrderItem(
        name="Маргарита",
        quantity=2,
    )

    assert item.name == "Маргарита"
    assert item.quantity == 2


def test_order_item_quantity_must_be_positive():
    with pytest.raises(ValidationError):
        OrderItem(
            name="Маргарита",
            quantity=0,
        )


def test_order_item_negative_quantity():
    with pytest.raises(ValidationError):
        OrderItem(
            name="Маргарита",
            quantity=-1,
        )


def test_multi_order_valid():
    order = MultiOrder(
        items=[
            OrderItem(
                name="Маргарита",
                quantity=2,
            )
        ],
        address="Победа 22",
    )

    assert len(order.items) == 1
    assert order.address == "Победа 22"
    assert order.status == "новый"


def test_multi_order_empty_address():
    with pytest.raises(ValidationError):
        MultiOrder(
            items=[
                OrderItem(
                    name="Маргарита",
                    quantity=2,
                )
            ],
            address="",
        )


def test_multi_order_multiple_pizzas():
    order = MultiOrder(
        items=[
            OrderItem(name="Маргарита", quantity=2),
            OrderItem(name="Песта", quantity=3),
        ],
        address="Победа 22",
    )

    assert len(order.items) == 2
    assert order.items[0].name == "Маргарита"
    assert order.items[1].name == "Песта"

