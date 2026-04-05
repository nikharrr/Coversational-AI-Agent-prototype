from __future__ import annotations

import logging

from app.models.schemas import Product
from app.services.groq_service import GroqService


logger = logging.getLogger(__name__)


class ExplanationService:
    def __init__(self, groq_service: GroqService) -> None:
        self.groq_service = groq_service

    def _fallback_explanation(self, product: Product, query: str) -> str:
        highlights = ", ".join(f"{key}: {value}" for key, value in product.attributes.items())
        return (
            f"{product.name} was recommended for '{query}' because its key traits match the need: "
            f"{highlights}. It also fits through {product.description.lower()}."
        )

    def explain(self, product: Product, query: str) -> str:
        logger.info("Generating explanation for product_id=%s", product.id)
        messages = [
            {
                "role": "system",
                "content": (
                    "You explain shopping recommendations in 2 or 3 sentences. Stay faithful to the provided "
                    "product data and directly connect the explanation to the user's query."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User query: {query}\n"
                    f"Product name: {product.name}\n"
                    f"Category: {product.category}\n"
                    f"Description: {product.description}\n"
                    f"Attributes: {product.attributes}\n"
                    f"Tags: {product.tags}"
                ),
            },
        ]
        try:
            return self.groq_service.generate(messages, temperature=0.3)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Using fallback explanation: %s", exc)
            return self._fallback_explanation(product, query)
