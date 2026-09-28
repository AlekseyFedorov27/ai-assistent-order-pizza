from decimal import Decimal

from modules.database.models import ProductDB
from modules.repositories.product import ProductRepository
from modules.schemas import Product


def test_get_by_name_returns_product(session):
    product = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    session.add(product)
    session.commit()

    repository = ProductRepository(session)

    result = repository.get_by_name("Маргарита")

    assert result is not None
    assert result.name == "Маргарита"
    assert result.price == Decimal("339.00")
    assert result.category == "Пицца"


def test_get_by_name_returns_none_for_unknown_product(session):
    repository = ProductRepository(session)

    result = repository.get_by_name("Пепперони")

    assert result is None


def test_get_all_returns_all_products(session):
    products = [
        ProductDB(
            name="Маргарита",
            price=Decimal("339.00"),
            category="Пицца",
        ),
        ProductDB(
            name="Пепперони",
            price=Decimal("450.00"),
            category="Пицца",
        ),
        ProductDB(
            name="Песта",
            price=Decimal("800.00"),
            category="Пицца",
        ),
    ]

    session.add_all(products)
    session.commit()

    repository = ProductRepository(session)

    result = repository.get_all()

    assert len(result) == 3
    assert {product.name for product in result} == {
        "Маргарита",
        "Пепперони",
        "Песта",
    }


def test_get_all_returns_products_sorted_by_name(session):
    products = [
        ProductDB(
            name="Песта",
            price=Decimal("800.00"),
            category="Пицца",
        ),
        ProductDB(
            name="Маргарита",
            price=Decimal("339.00"),
            category="Пицца",
        ),
        ProductDB(
            name="Пепперони",
            price=Decimal("450.00"),
            category="Пицца",
        ),
    ]

    session.add_all(products)
    session.commit()

    repository = ProductRepository(session)

    result = repository.get_all()

    assert [product.name for product in result] == [
        "Маргарита",
        "Пепперони",
        "Песта",
    ]


def test_create_product(session):
    repository = ProductRepository(session)

    product = Product(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    result = repository.create(product)

    assert result.id is not None
    assert result.name == "Маргарита"
    assert result.price == Decimal("339.00")
    assert result.category == "Пицца"

    session.commit()

    saved_product = session.get(ProductDB, result.id)

    assert saved_product is not None
    assert saved_product.name == "Маргарита"