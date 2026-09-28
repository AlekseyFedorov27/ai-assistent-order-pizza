class FakeOrderItem:
    def __init__(self, name, quantity, price, subtotal):
        self.name = name
        self.quantity = quantity
        self.price = price
        self.subtotal = subtotal


class FakeOrderResponse:
    """Минимальный объект, совместимый по полям с OrderResponse."""

    def __init__(self):
        self.id = 1
        self.user_id = 1
        self.items = [
            FakeOrderItem(
                name="Маргарита",
                quantity=2,
                price=Decimal("339"),
                subtotal=Decimal("678"),
            )
        ]
        self.address = "Победа 22"
        self.total = Decimal("678")
        self.status = "новый"
        self.created_at = datetime(2026, 1, 1, 12, 0, 0)