from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import configure_logging, settings
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ExplainRequest,
    ExplainResponse,
    HealthResponse,
    SearchRequest,
    SearchResponse,
    UsersResponse,
)
from app.services.catalog_service import CatalogService
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.explanation_service import ExplanationService
from app.services.groq_service import GroqService
from app.services.search_service import SearchService


configure_logging()
logger = logging.getLogger(__name__)


class ServiceContainer:
    def __init__(self) -> None:
        self.catalog_service = CatalogService()
        self.embedding_service = EmbeddingService()
        self.groq_service = GroqService()
        self.search_service = SearchService(
            embedding_service=self.embedding_service,
            catalog_service=self.catalog_service,
        )
        self.chat_service = ChatService(
            search_service=self.search_service,
            catalog_service=self.catalog_service,
            groq_service=self.groq_service,
        )
        self.explanation_service = ExplanationService(groq_service=self.groq_service)


container: ServiceContainer | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global container
    logger.info("Starting %s", settings.app_name)
    container = ServiceContainer()
    container.search_service.ingest_products(container.catalog_service.products)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_container() -> ServiceContainer:
    if container is None:
        raise RuntimeError("Service container is not initialized")
    return container


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/users", response_model=UsersResponse)
def list_users() -> UsersResponse:
    services = get_container()
    return UsersResponse(users=services.catalog_service.users)


@app.post("/ingest-products")
def ingest_products() -> dict[str, Any]:
    services = get_container()
    services.catalog_service.refresh()
    return services.search_service.ingest_products(services.catalog_service.products)


@app.post("/search", response_model=SearchResponse)
def search_products(request: SearchRequest) -> SearchResponse:
    services = get_container()
    results = services.search_service.search(request.query)
    return SearchResponse(query=request.query, results=results)


@app.post("/chat", response_model=ChatResponse)
def chat_assistant(request: ChatRequest) -> ChatResponse:
    services = get_container()
    return services.chat_service.chat(user_id=request.user_id, message=request.message)


@app.post("/explain", response_model=ExplainResponse)
def explain_recommendation(request: ExplainRequest) -> ExplainResponse:
    services = get_container()
    product = services.catalog_service.get_product(request.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    explanation = services.explanation_service.explain(product=product, query=request.query)
    return ExplainResponse(product_id=request.product_id, explanation=explanation)
