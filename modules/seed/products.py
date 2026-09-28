from ..schemas import Product
from ..services.product import ProductService
from ..database.session import SessionLocal


PRODUCTS: list[Product] = [
    Product(
        name="Пепперони",
        price=239,
        category="пицца",
    ),
    Product(
        name="Четыре сыра",
        price=339,
        category="пицца",
    ),
    Product(
        name="Карбонара",
        price=409,
        category="паста",
    ),
    Product(
        name="Песта",
        price=389,
        category="паста",
    ),
    Product(
        name="Маргарита",
        price=339,
        category="пицца",
    ),
]


def init_products() -> None:

    with SessionLocal() as session:

        service = ProductService(session)

        for product in PRODUCTS:
            try:
                service.create_product(product)

            except ValueError as e:
                print(
                    f"⚠️ {e}"
                )