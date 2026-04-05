from __future__ import annotations

import logging

from sentence_transformers import SentenceTransformer

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        logger.info("Loading embedding model %s", settings.embedding_model_name)
        self.model = SentenceTransformer(settings.embedding_model_name)

    def embed_text(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
