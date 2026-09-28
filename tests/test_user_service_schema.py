from decimal import Decimal
from datetime import datetime

from modules.database.models import OrderDB
from modules.services.user import UserService


def test_to_schema_converts_order_to_order_response():
    """
    ORM-модель OrderDB должна корректно
    преобразовываться в Pydantic OrderResponse.
    """

    order = OrderDB(
        id=1,
        user_id=10,
        items=[
            {
                "name": "Маргарита",
                "price": "339.00",
                "quantity": 2,
                "subtotal": "678.00",
            }
        ],
        address="Победа 22",
        total=Decimal("678.00"),
        status="новый",
        created_at=datetime(2026, 9, 10, 12, 0, 0),
    )

    result = UserService._to_schema(order)

    assert result.id == 1
    assert result.user_id == 10
    assert result.address == "Победа 22"
    assert result.total == Decimal("678.00")
    assert result.status == "новый"

    assert len(result.items) == 1
    assert result.items[0].name == "Маргарита"
    assert result.items[0].quantity == 2