from types import SimpleNamespace

from modules.tools.order import save_order


def test_save_order_creates_order(monkeypatch):

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class FakeOrderService:
        def __init__(self, session):
            pass

        def create_order(
            self,
            *,
            user_id,
            items,
            address,
            status,
        ):
            assert user_id == 1
            assert address == "Победа 22"
            assert status == "новый"

            assert len(items) == 1
            assert items[0].name == "Маргарита"
            assert items[0].quantity == 2

            return SimpleNamespace(id=123)

    monkeypatch.setattr(
        "modules.tools.order.SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        "modules.tools.order.OrderService",
        FakeOrderService,
    )

    # save_order берёт user_id из ContextVar через get_user_id(),
    # а не из config — поэтому мокаем именно get_user_id.
    monkeypatch.setattr(
        "modules.tools.order.get_user_id",
        lambda: 1,
    )

    result = save_order.invoke({
        "items": [
            {
                "name": "Маргарита",
                "quantity": 2,
            }
        ],
        "address": "Победа 22",
        "status": "новый",
    })

    assert result == "Заказ #123 успешно сохранён!"


def test_save_order_propagates_service_error(monkeypatch):

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class FakeOrderService:
        def __init__(self, session):
            pass

        def create_order(self, **kwargs):
            raise ValueError("Ошибка создания заказа")

    monkeypatch.setattr(
        "modules.tools.order.SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        "modules.tools.order.OrderService",
        FakeOrderService,
    )

    monkeypatch.setattr(
        "modules.tools.order.get_user_id",
        lambda: 1,
    )

    try:
        save_order.invoke({
            "items": [
                {
                    "name": "Маргарита",
                    "quantity": 2,
                }
            ],
            "address": "Победа 22",
            "status": "новый",
        })

        assert False, "Ожидалось исключение ValueError"

    except ValueError as exc:
        assert str(exc) == "Ошибка создания заказа"