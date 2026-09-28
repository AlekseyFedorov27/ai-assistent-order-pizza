from unittest.mock import Mock

import pytest

from modules.services.user import UserService


def create_service():
    session = Mock()

    service = UserService(
        session=session,
    )

    return service


def test_update_address():
    """
    Адрес пользователя должен обновляться,
    а транзакция должна завершаться commit.
    """

    service = create_service()

    service.user_repository.update_address = Mock()

    result = service.update_address(
        user_id=1,
        address="Победа 22",
    )

    assert result == "Победа 22"

    service.user_repository.update_address.assert_called_once_with(
        user_id=1,
        address="Победа 22",
    )

    service.session.commit.assert_called_once()
    service.session.rollback.assert_not_called()


def test_update_address_rolls_back_on_error():
    """
    Если обновление адреса завершается ошибкой,
    должен выполняться rollback.
    """

    service = create_service()

    service.user_repository.update_address = Mock(
        side_effect=Exception("Database error")
    )

    with pytest.raises(
        Exception,
        match="Database error",
    ):
        service.update_address(
            user_id=1,
            address="Победа 22",
        )

    service.session.rollback.assert_called_once()
    service.session.commit.assert_not_called()


def test_update_last_order_id():
    """
    last_order_id должен обновляться,
    а транзакция должна завершаться commit.
    """

    service = create_service()

    service.user_repository.update_last_order_id = Mock()

    service.update_last_order_id(
        user_id=1,
        order_id=15,
    )

    service.user_repository.update_last_order_id.assert_called_once_with(
        user_id=1,
        order_id=15,
    )

    service.session.commit.assert_called_once()
    service.session.rollback.assert_not_called()


def test_update_last_order_id_rolls_back_on_error():
    """
    Если обновление last_order_id завершается ошибкой,
    должен выполняться rollback.
    """

    service = create_service()

    service.user_repository.update_last_order_id = Mock(
        side_effect=Exception("Database error")
    )

    with pytest.raises(
        Exception,
        match="Database error",
    ):
        service.update_last_order_id(
            user_id=1,
            order_id=15,
        )

    service.session.rollback.assert_called_once()
    service.session.commit.assert_not_called()