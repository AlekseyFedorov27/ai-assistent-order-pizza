from decimal import Decimal
from unittest.mock import Mock

import pytest

from modules.schemas import OrderItem
from modules.services.order import OrderService


def create_service():
    session = Mock()

    service = OrderService(session)

    service.product_repository = Mock()
    service.order_repository = Mock()
    service.user_repository = Mock()

    return service


def test_create_order():
    """
    Заказ должен быть создан и сохранён.
    """

    service = create_service()

    # Подготавливаем товар
    product = Mock()
    product.name = "Маргарита"
    product.price = Decimal("339.00")

    service.product_repository.get_by_name.return_value = product

    # Имитируем созданный заказ
    order = Mock()
    order.id = 1

    service.order_repository.create.return_value = order

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        )
    ]

    result = service.create_order(
        user_id="4",
        items=items,
        address="Лугова 45",
        status="новый",
    )

    # Должен вернуться созданный заказ
    assert result == order

    # Проверяем, что repository действительно вызвался
    service.order_repository.create.assert_called_once()

    # Проверяем commit
    service.session.commit.assert_called_once()


def test_create_order_calculates_total():
    """
    При создании заказа total должен рассчитываться
    на основании цены товара из базы.
    """

    service = create_service()

    product = Mock()
    product.name = "Маргарита"
    product.price = Decimal("339.00")

    service.product_repository.get_by_name.return_value = product

    order = Mock()
    order.id = 1

    service.order_repository.create.return_value = order

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        )
    ]

    service.create_order(
        user_id="4",
        items=items,
        address="Лугова 45",
        status="новый",
    )

    service.order_repository.create.assert_called_once()

    call_kwargs = service.order_repository.create.call_args.kwargs

    assert call_kwargs["total"] == Decimal("678.00")


def test_create_order_passes_user_id():
    """
    user_id должен передаваться в OrderRepository
    как integer.
    """

    service = create_service()

    product = Mock()
    product.name = "Маргарита"
    product.price = Decimal("339.00")

    service.product_repository.get_by_name.return_value = product

    order = Mock()
    order.id = 10

    service.order_repository.create.return_value = order

    items = [
        OrderItem(
            name="Маргарита",
            quantity=1,
        )
    ]

    service.create_order(
        user_id="4",
        items=items,
        address="Лугова 45",
        status="новый",
    )

    call_kwargs = service.order_repository.create.call_args.kwargs

    assert call_kwargs["user_id"] == 4


def test_create_order_updates_user():
    """
    После создания заказа информация о последнем заказе
    должна сохраняться у пользователя.
    """

    service = create_service()

    product = Mock()
    product.name = "Маргарита"
    product.price = Decimal("339.00")

    service.product_repository.get_by_name.return_value = product

    order = Mock()
    order.id = 5

    service.order_repository.create.return_value = order

    items = [
        OrderItem(
            name="Маргарита",
            quantity=2,
        )
    ]

    service.create_order(
        user_id="4",
        items=items,
        address="Лугова 45",
        status="новый",
    )

    service.user_repository.update_last_orders.assert_called_once()

    call_kwargs = (
        service.user_repository
        .update_last_orders
        .call_args
        .kwargs
    )

    assert call_kwargs["user_id"] == 4

    assert call_kwargs["last_order"]["order_id"] == 5
    assert call_kwargs["last_order"]["address"] == "Лугова 45"
    assert call_kwargs["last_order"]["status"] == "новый"
    assert call_kwargs["last_order"]["total"] == "678.00"


def test_create_order_updates_last_order_id():
    """
    После создания заказа last_order_id пользователя
    должен быть обновлён.
    """

    service = create_service()

    product = Mock()
    product.name = "Маргарита"
    product.price = Decimal("339.00")

    service.product_repository.get_by_name.return_value = product

    order = Mock()
    order.id = 7

    service.order_repository.create.return_value = order

    items = [
        OrderItem(
            name="Маргарита",
            quantity=1,
        )
    ]

    service.create_order(
        user_id="4",
        items=items,
        address="Лугова 45",
        status="новый",
    )

    service.user_repository.update_last_order_id.assert_called_once_with(
        user_id=4,
        order_id=7,
    )


def test_create_order_updates_address():
    """
    Адрес пользователя должен обновляться после создания заказа.
    """

    service = create_service()

    product = Mock()
    product.name = "Маргарита"
    product.price = Decimal("339.00")

    service.product_repository.get_by_name.return_value = product

    order = Mock()
    order.id = 1

    service.order_repository.create.return_value = order

    items = [
        OrderItem(
            name="Маргарита",
            quantity=1,
        )
    ]

    service.create_order(
        user_id="4",
        items=items,
        address="Победа 22",
        status="новый",
    )

    service.user_repository.update_address.assert_called_once_with(
        user_id=4,
        address="Победа 22",
    )


def test_create_order_rolls_back_on_error():
    """
    Если при создании заказа возникает ошибка,
    транзакция должна быть отменена через rollback.
    """

    service = create_service()

    service.product_repository.get_by_name.side_effect = Exception(
        "Database error"
    )

    items = [
        OrderItem(
            name="Маргарита",
            quantity=1,
        )
    ]

    with pytest.raises(Exception, match="Database error"):
        service.create_order(
            user_id="4",
            items=items,
            address="Лугова 45",
            status="новый",
        )

    service.session.rollback.assert_called_once()

    service.session.commit.assert_not_called()

