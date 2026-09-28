from unittest.mock import Mock

import pytest

from modules.services.user import UserService


def create_service(store=None):
    session = Mock()

    service = UserService(
        session=session,
        store=store,
    )

    return service


def test_load_user_to_store_saves_user():
    """
    Данные существующего пользователя должны
    сохраняться в Store.
    """

    store = Mock()
    service = create_service(store=store)

    user = Mock()
    user.user_id = 1
    user.address = "Победа 22"
    user.last_order_id = 5
    user.last_orders = [
        {
            "order_id": 5,
            "total": "678.00",
        }
    ]

    service.user_repository.get_by_id = Mock(
        return_value=user
    )

    result = service.load_user_to_store(1)

    assert result == user

    store.put.assert_called_once_with(
        ("users",),
        "1",
        {
            "user_id": 1,
            "address": "Победа 22",
            "last_order_id": 5,
            "last_orders": [
                {
                    "order_id": 5,
                    "total": "678.00",
                }
            ],
        },
    )


def test_load_user_to_store_returns_none_for_unknown_user():
    """
    Если пользователя нет в БД,
    в Store ничего записываться не должно.
    """

    store = Mock()
    service = create_service(store=store)

    service.user_repository.get_by_id = Mock(
        return_value=None
    )

    result = service.load_user_to_store(999)

    assert result is None

    store.put.assert_not_called()


def test_load_user_to_store_requires_store():
    """
    Нельзя загрузить пользователя в Store,
    если Store не передан в UserService.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Store не передан в UserService",
    ):
        service.load_user_to_store(1)