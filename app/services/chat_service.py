from __future__ import annotations

import logging

from app.models.schemas import ChatResponse, Product, User
from app.services.catalog_service import CatalogService
from app.services.groq_service import GroqService
from app.services.search_service import SearchService


logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        search_service: SearchService,
        catalog_service: CatalogService,
        groq_service: GroqService,
    ) -> None:
        self.search_service = search_service
        self.catalog_service = catalog_service
        self.groq_service = groq_service
        self.conversation_history: dict[str, list[dict[str, str]]] = {}

    def _format_recommendations(self, products: list[Product]) -> str:
        return "\n".join(
            [
                (
                    f"- {product.name} ({product.category}, Rs. {product.price}): "
                    f"{product.description}. Attributes: {product.attributes}. Tags: {product.tags}"
                )
                for product in products
            ]
        )

    def _build_user_context(self, user: User | None, user_id: str) -> str:
        if user is None:
            return f"User ID: {user_id}. No saved profile found."

        purchase_history = self.catalog_service.get_user_purchase_history(user_id)
        history_summary = ", ".join(
            f"{record.product_id} on {record.date} ({record.category})" for record in purchase_history[-5:]
        ) or "No purchase history."
        return (
            f"User ID: {user.id}\n"
            f"Name: {user.name}\n"
            f"Age: {user.age}\n"
            f"Location: {user.location}\n"
            f"Preferences: {', '.join(user.preferences)}\n"
            f"Recent purchases: {history_summary}"
        )

    def _fallback_response(self, message: str, products: list[Product]) -> str:
        if not products:
            return (
                "I could not find a strong product match yet. If you share the category, budget, or style, "
                "I can narrow it down."
            )

        lead = products[0]
        return (
            f"I recommend {lead.name} because it aligns with your request for {message.lower()}. "
            f"It stands out for {lead.description.lower()}."
        )

    def chat(self, user_id: str, message: str) -> ChatResponse:
        logger.info("Handling chat for user_id=%s", user_id)
        recommendations = [item.product for item in self.search_service.search(message)]
        user = self.catalog_service.get_user(user_id)

        system_prompt = (
            "You are a warm, concise shopping assistant. Use the retrieved products to recommend up to 3 items. "
            "Explain why each item fits the user's need, mention trade-offs when relevant, and stay grounded in "
            "the provided product data."
        )
        conversation = self.conversation_history.setdefault(user_id, [])
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": self._build_user_context(user, user_id)},
            {
                "role": "system",
                "content": "Relevant products:\n" + self._format_recommendations(recommendations[:3]),
            },
            *conversation[-6:],
            {"role": "user", "content": message},
        ]

        try:
            response_text = self.groq_service.generate(messages)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falling back to template response: %s", exc)
            response_text = self._fallback_response(message, recommendations)

        conversation.extend(
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response_text},
            ]
        )
        return ChatResponse(
            user_id=user_id,
            response=response_text,
            recommendations=recommendations[:3],
        )
