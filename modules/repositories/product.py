from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database.models import ProductDB
from ..schemas import Product


class ProductRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_name(
        self,
        name: str,
    ) -> ProductDB | None:

        stmt = select(ProductDB).where(
            ProductDB.name == name
        )

        return self.session.scalar(stmt)

    def get_all(self) -> list[ProductDB]:

        stmt = select(ProductDB).order_by(
            ProductDB.name
        )

        return list(
            self.session.scalars(stmt).all()
        )

    def create(
        self,
        product: Product,
    ) -> ProductDB:

        db_product = ProductDB(
            name=product.name,
            price=product.price,
            category=product.category,
        )

        self.session.add(db_product)

        # Получаем id до commit
        self.session.flush()

        return db_product