from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..repositories.product import ProductRepository
from ..database.models import ProductDB
from ..schemas import Product


class ProductService:

    def __init__(self, session: Session):
        self.session = session
        self.repository = ProductRepository(session)

    def create_product(
        self,
        product: Product,
    ) -> Product:

        existing = self.repository.get_by_name(
            product.name
        )

        if existing:
            raise ValueError(
                f"Товар '{product.name}' уже существует"
            )

        try:
            db_product = self.repository.create(product)

            self.session.commit()
            self.session.refresh(db_product)

            return self._to_schema(db_product)

        except IntegrityError:
            self.session.rollback()

            raise ValueError(
                f"Товар '{product.name}' уже существует"
            )

        except Exception:
            self.session.rollback()
            raise

    def get_product(
        self,
        name: str,
    ) -> Product | None:

        db_product = self.repository.get_by_name(name)

        if db_product is None:
            return None

        return self._to_schema(db_product)

    def get_all_products(self) -> list[Product]:

        products = self.repository.get_all()

        return [
            self._to_schema(product)
            for product in products
        ]

    @staticmethod
    def _to_schema(product: ProductDB) -> Product:
        return Product(
            name=product.name,
            price=product.price,
            category=str(product.category),
        )