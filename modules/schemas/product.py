from pydantic import BaseModel, Field
from decimal import Decimal


class Product(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    price: Decimal

    category: str = Field(
        default='',
        max_length=50,
    )

