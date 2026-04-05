from __future__ import annotations

import logging
from typing import Any

import requests

from app.core.config import settings


logger = logging.getLogger(__name__)


class GroqService:
    def __init__(self) -> None:
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, messages: list[dict[str, str]], temperature: float = 0.4) -> str:
        if not self.is_configured():
            logger.warning("GROQ_API_KEY is not configured; using local fallback response")
            raise RuntimeError("GROQ_API_KEY is not configured")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
