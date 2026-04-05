from __future__ import annotations

import json
import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.models.schemas import Product, ProductSearchResult
from app.services.catalog_service import CatalogService
from app.services.embedding_service import EmbeddingService


logger = logging.getLogger(__name__)


class SearchService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        catalog_service: CatalogService,
    ) -> None:
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        self.embedding_service = embedding_service
        self.catalog_service = catalog_service
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"description": "Shopping assistant products"},
        )

    @staticmethod
    def _build_document(product: Product) -> str:
        return (
            f"Name: {product.name}\n"
            f"Category: {product.category}\n"
            f"Description: {product.description}\n"
            f"Attributes: {json.dumps(product.attributes, ensure_ascii=True)}\n"
            f"Tags: {', '.join(product.tags)}"
        )

    def ingest_products(self, products: list[Product]) -> dict[str, Any]:
        logger.info("Ingesting %s products into Chroma", len(products))
        if not products:
            return {"ingested_count": 0, "collection_name": settings.chroma_collection_name}

        ids = [product.id for product in products]
        documents = [self._build_document(product) for product in products]
        embeddings = self.embedding_service.embed_documents(documents)
        metadatas = [
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "tags": ", ".join(product.tags),
            }
            for product in products
        ]

        existing = self.collection.get(ids=ids)
        existing_ids = set(existing["ids"]) if existing["ids"] else set()
        if existing_ids:
            self.collection.delete(ids=list(existing_ids))

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return {
            "ingested_count": len(products),
            "collection_name": settings.chroma_collection_name,
        }

    def search(self, query: str, top_k: int | None = None) -> list[ProductSearchResult]:
        limit = top_k or settings.top_k
        logger.info("Searching products for query=%s", query)
        query_embedding = self.embedding_service.embed_text(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["metadatas", "distances"],
        )

        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]

        search_results: list[ProductSearchResult] = []
        for product_id, distance in zip(ids, distances):
            product = self.catalog_service.get_product(product_id)
            if product is None:
                continue
            similarity_score = max(0.0, 1 - float(distance))
            search_results.append(
                ProductSearchResult(product=product, similarity_score=round(similarity_score, 4))
            )
        return search_results
