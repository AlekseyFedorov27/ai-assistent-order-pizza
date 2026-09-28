import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from modules.database.models import ProductDB
from modules.schemas import Product
from modules.services.product import ProductService


def test_create_product(session):
    service = ProductService(session)

    product = Product(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    result = service.create_product(product)

    assert isinstance(result, Product)
    assert result.name == "Маргарита"
    assert result.price == Decimal("339.00")
    assert result.category == "Пицца"

    saved_product = session.query(ProductDB).one()

    assert saved_product.name == "Маргарита"
    assert saved_product.price == Decimal("339.00")


def test_create_product_rejects_duplicate(session):
    existing = ProductDB(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    session.add(existing)
    session.commit()

    service = ProductService(session)

    product = Product(
        name="Маргарита",
        price=Decimal("450.00"),
        category="Пицца",
    )

    with pytest.raises(
        ValueError,
        match="Товар 'Маргарита' уже существует",
    ):
        service.create_product(product)

    products = session.query(ProductDB).all()

    assert len(products) == 1
    assert products[0].price == Decimal("339.00")


def test_get_product_returns_product(session):
    product = ProductDB(
        name="Пепперони",
        price=Decimal("450.00"),
        category="Пицца",
    )

    session.add(product)
    session.commit()

    service = ProductService(session)

    result = service.get_product("Пепперони")

    assert result is not None
    assert isinstance(result, Product)
    assert result.name == "Пепперони"
    assert result.price == Decimal("450.00")
    assert result.category == "Пицца"


def test_get_product_returns_none_for_unknown_product(session):
    service = ProductService(session)

    result = service.get_product("Несуществующая пицца")

    assert result is None


def test_get_all_products_returns_products(session):
    products = [
        ProductDB(
            name="Пепперони",
            price=Decimal("450.00"),
            category="Пицца",
        ),
        ProductDB(
            name="Маргарита",
            price=Decimal("339.00"),
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

    service = ProductService(session)

    result = service.get_all_products()

    assert len(result) == 3

    assert [product.name for product in result] == [
        "Маргарита",
        "Пепперони",
        "Песта",
    ]


def test_get_all_products_returns_empty_list(session):
    service = ProductService(session)

    result = service.get_all_products()

    assert result == []


def test_create_product_rolls_back_on_error(session, monkeypatch):
    service = ProductService(session)

    product = Product(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    def broken_create(*args, **kwargs):
        raise RuntimeError("Ошибка создания товара")

    monkeypatch.setattr(
        service.repository,
        "create",
        broken_create,
    )

    with pytest.raises(
        RuntimeError,
        match="Ошибка создания товара",
    ):
        service.create_product(product)

    products = session.query(ProductDB).all()

    assert products == []

def test_create_product_handles_integrity_error(
    session,
    monkeypatch,
):
    service = ProductService(session)

    product = Product(
        name="Маргарита",
        price=Decimal("339.00"),
        category="Пицца",
    )

    def broken_create(*args, **kwargs):
        raise IntegrityError(
            "INSERT",
            {},
            Exception("UNIQUE constraint failed"),
        )

    monkeypatch.setattr(
        service.repository,
        "create",
        broken_create,
    )

    with pytest.raises(
        ValueError,
        match="Товар 'Маргарита' уже существует",
    ):
        service.create_product(product)

    products = session.query(ProductDB).all()

    assert products == []    