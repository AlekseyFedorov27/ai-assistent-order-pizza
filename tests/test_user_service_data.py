from unittest.mock import Mock

from modules.services.user import UserService


def create_service():
    session = Mock()

    service = UserService(
        session=session,
    )

    return service


def test_get_user_data_returns_user():
    """
    get_user_data должен вернуть пользователя,
    если он существует.
    """

    service = create_service()

    user = Mock()
    user.user_id = 1
    user.user_name = "Алексей"

    service.user_repository.get_by_id = Mock(
        return_value=user
    )

    result = service.get_user_data(
        user_id=1,
    )

    assert result is user

    service.user_repository.get_by_id.assert_called_once_with(
        1
    )


def test_get_user_data_returns_none_for_unknown_user():
    """
    Если пользователя нет, get_user_data должен вернуть None.
    """

    service = create_service()

    service.user_repository.get_by_id = Mock(
        return_value=None
    )

    result = service.get_user_data(
        user_id=999,
    )

    assert result is None

    service.user_repository.get_by_id.assert_called_once_with(
        999
    )