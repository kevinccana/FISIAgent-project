from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any, Optional, Protocol


class ResourceSource(Protocol):
    """Contract for loading district data from any backend."""

    def load_distritos(self) -> list[dict[str, Any]]:
        ...


class JsonResourceSource:
    """Loads district data from a JSON file with configurable keys."""

    def __init__(
        self,
        json_path: str | Path = "recursos_lima.json",
        distritos_key: str = "distritos",
    ) -> None:
        self.json_path = Path(json_path)
        self.distritos_key = distritos_key

    def load_distritos(self) -> list[dict[str, Any]]:
        if not self.json_path.exists():
            raise FileNotFoundError(
                f"Resource file not found: {self.json_path.resolve()}"
            )

        try:
            with self.json_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON format in file: {self.json_path.resolve()}"
            ) from exc

        distritos = payload.get(self.distritos_key)
        if not isinstance(distritos, list):
            raise ValueError(
                f"Invalid structure: key '{self.distritos_key}' must be a list."
            )

        return distritos


class MongoResourceSource:
    """Loads district data from a MongoDB collection."""

    def __init__(self, uri: str, database: str, collection: str) -> None:
        self.uri = uri
        self.database = database
        self.collection = collection

    def load_distritos(self) -> list[dict[str, Any]]:
        try:
            from pymongo import MongoClient  # type: ignore[import-not-found]
            from pymongo.errors import PyMongoError  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "Missing dependency 'pymongo'. Install it with: pip install pymongo"
            ) from exc

        try:
            with MongoClient(self.uri, serverSelectionTimeoutMS=3000) as client:
                docs = list(
                    client[self.database][self.collection].find(
                        {},
                        {"_id": 0, "nombre": 1, "keywords": 1, "recursos": 1},
                    )
                )
        except PyMongoError as exc:
            raise ConnectionError(
                "Could not load resources from MongoDB. Check URI and collection."
            ) from exc

        if not isinstance(docs, list):
            raise ValueError("Invalid MongoDB payload: expected a list of districts.")

        return docs


class ResourceManager:
    """Queries mental health resources by district keywords."""

    def __init__(self, source: ResourceSource | None = None) -> None:
        json_path = Path(__file__).parent / "recursos_lima.json"
        self.source = source or JsonResourceSource(json_path)
        self._distritos: list[dict[str, Any]] = self.source.load_distritos()

    @classmethod
    def from_json(
        cls,
        json_path: str | Path = "recursos_lima.json",
        distritos_key: str = "distritos",
    ) -> ResourceManager:
        return cls(JsonResourceSource(json_path=json_path, distritos_key=distritos_key))

    @classmethod
    def from_mongo(cls, uri: str, database: str, collection: str) -> ResourceManager:
        return cls(MongoResourceSource(uri=uri, database=database, collection=collection))

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Converts text to lowercase and removes accent marks."""
        text = text.lower().strip()
        normalized = unicodedata.normalize("NFD", text)
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def buscar_por_distrito(self, mensaje: str) -> Optional[list[dict[str, Any]]]:
        """Returns resources list if any district keyword is found in the message."""
        if not isinstance(mensaje, str) or not mensaje.strip():
            return None

        mensaje_normalizado = self._normalize_text(mensaje)

        for distrito in self._distritos:
            keywords = distrito.get("keywords", [])
            if not isinstance(keywords, list):
                continue

            for keyword in keywords:
                if not isinstance(keyword, str):
                    continue

                keyword_normalizado = self._normalize_text(keyword)
                if keyword_normalizado and keyword_normalizado in mensaje_normalizado:
                    recursos = distrito.get("recursos")
                    return recursos if isinstance(recursos, list) else None

        return None
