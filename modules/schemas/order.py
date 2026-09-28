from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal

class OrderItem(BaseModel):
    name: str
    quantity: int = Field(
        ge=1,
    )

class OrderItemResponse(BaseModel):
    name: str
    price: Decimal
    quantity: int
    subtotal: Decimal


class MultiOrder(BaseModel):
    items: list[OrderItem]

    address: str = Field(
        min_length=1,
        max_length=200,
    )

    status: str = "новый"

class OrderResponse(BaseModel):
    id: int
    user_id: int
    items: list[OrderItemResponse]
    address: str
    total: Decimal
    status: str
    created_at: datetime   


class OrderItemPreview(BaseModel):
    name: str
    quantity: int
    price: Decimal
    subtotal: Decimal


class OrderPreview(BaseModel):
    items: list[OrderItemPreview]
    address: str
    status: str
    total: Decimal
