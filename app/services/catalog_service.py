from __future__ import annotations

import logging

from app.core.config import settings
from app.core.data_loader import load_json_file
from app.models.schemas import Product, PurchaseRecord, User


logger = logging.getLogger(__name__)


class CatalogService:
    def __init__(self) -> None:
        self.products: list[Product] = []
        self.users: list[User] = []
        self.purchase_history: list[PurchaseRecord] = []
        self.products_by_id: dict[str, Product] = {}
        self.users_by_id: dict[str, User] = {}
        self.refresh()

    def _load_products(self) -> list[Product]:
        logger.info("Loading products from %s", settings.products_path)
        return [Product.model_validate(item) for item in load_json_file(settings.products_path)]

    def _load_users(self) -> list[User]:
        logger.info("Loading users from %s", settings.users_path)
        return [User.model_validate(item) for item in load_json_file(settings.users_path)]

    def _load_purchase_history(self) -> list[PurchaseRecord]:
        logger.info("Loading purchase history from %s", settings.purchase_history_path)
        return [
            PurchaseRecord.model_validate(item)
            for item in load_json_file(settings.purchase_history_path)
        ]

    def get_product(self, product_id: str) -> Product | None:
        return self.products_by_id.get(product_id)

    def get_user(self, user_id: str) -> User | None:
        return self.users_by_id.get(user_id)

    def get_user_purchase_history(self, user_id: str) -> list[PurchaseRecord]:
        return [record for record in self.purchase_history if record.user_id == user_id]

    def refresh(self) -> None:
        self.products = self._load_products()
        self.users = self._load_users()
        self.purchase_history = self._load_purchase_history()
        self.products_by_id = {product.id: product for product in self.products}
        self.users_by_id = {user.id: user for user in self.users}
