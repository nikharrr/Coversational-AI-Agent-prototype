from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "storage" / "chroma"

load_dotenv(BASE_DIR / ".env")


@dataclass(slots=True)
class Settings:
    app_name: str = "Conversational AI Shopping Assistant"
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_collection_name: str = "products_collection"
    chroma_path: Path = CHROMA_DIR
    products_path: Path = DATA_DIR / "products.json"
    users_path: Path = DATA_DIR / "users.json"
    purchase_history_path: Path = DATA_DIR / "purchase_history.json"
    top_k: int = 5


settings = Settings()


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
