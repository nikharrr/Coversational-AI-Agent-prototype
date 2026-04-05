from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    category: str
    description: str
    price: float
    attributes: dict[str, Any]
    tags: list[str]


class User(BaseModel):
    id: str
    name: str
    age: int
    location: str
    preferences: list[str]


class PurchaseRecord(BaseModel):
    user_id: str
    product_id: str
    date: str
    price: float
    category: str


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2)


class ChatRequest(BaseModel):
    user_id: str
    message: str = Field(..., min_length=2)


class ExplainRequest(BaseModel):
    product_id: str
    query: str = Field(..., min_length=2)


class HealthResponse(BaseModel):
    status: str


class ProductSearchResult(BaseModel):
    product: Product
    similarity_score: float | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[ProductSearchResult]


class ChatResponse(BaseModel):
    user_id: str
    response: str
    recommendations: list[Product]


class ExplainResponse(BaseModel):
    product_id: str
    explanation: str


class UsersResponse(BaseModel):
    users: list[User]
