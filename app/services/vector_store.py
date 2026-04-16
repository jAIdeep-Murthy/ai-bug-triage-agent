"""
Vector store service: embeds bug descriptions and performs semantic search
using ChromaDB + sentence-transformers/all-MiniLM-L6-v2.
"""

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

COLLECTION_NAME = "historical_bugs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class VectorStore:
    """Wraps a persistent ChromaDB collection with sentence-transformer embeddings."""

    def __init__(self, db_path: str = "data/chroma_db"):
        db_root = Path(db_path)
        db_root.parent.mkdir(parents=True, exist_ok=True)
        db_root.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(db_root))
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
            device="cpu",
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
        )

    def count(self) -> int:
        """Return number of documents in the collection."""
        return int(self.collection.count())

    def upsert_bug(self, issue_key: str, text: str, metadata: dict) -> None:
        """Embed and upsert a single bug."""
        clean_metadata = {
            "severity": str(metadata.get("severity") or ""),
            "category": str(metadata.get("category") or ""),
            "owner_team": str(metadata.get("owner_team") or ""),
        }
        trimmed_text = (text or "").strip()[:512]
        self.collection.upsert(
            ids=[str(issue_key)],
            documents=[trimmed_text],
            metadatas=[clean_metadata],
        )

    def upsert_bugs_bulk(self, bugs: list[dict]) -> None:
        """Bulk upsert bugs in batches of 100."""
        if not bugs:
            return

        batch_size = 100
        total = len(bugs)
        total_batches = (total + batch_size - 1) // batch_size
        inserted = 0

        for idx in range(0, total, batch_size):
            batch = bugs[idx : idx + batch_size]
            ids: list[str] = []
            documents: list[str] = []
            metadatas: list[dict[str, str]] = []
            for bug in batch:
                issue_key = str(bug.get("issue_key") or "").strip()
                title = str(bug.get("title") or "").strip()
                description = str(bug.get("description") or "").strip()
                text = f"{title} {description}".strip()[:512]
                ids.append(issue_key)
                documents.append(text)
                metadatas.append(
                    {
                        "severity": str(bug.get("severity") or ""),
                        "category": str(bug.get("category") or ""),
                        "owner_team": str(bug.get("owner_team") or ""),
                    }
                )

            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            inserted += len(batch)
            batch_no = (idx // batch_size) + 1
            print(f"Indexed batch {batch_no}/{total_batches} ({inserted} total so far)")

    def semantic_search(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[dict]:
        """Return semantic hits from ChromaDB with similarity scores."""
        if self.count() == 0:
            return []

        kwargs: dict[str, Any] = {
            "query_texts": [query_text[:512]],
            "n_results": n_results,
        }
        if filter_metadata:
            kwargs["where"] = filter_metadata

        result = self.collection.query(**kwargs)
        ids = (result.get("ids") or [[]])[0]
        docs = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        out: list[dict] = []
        for issue_key, text, metadata, distance in zip(ids, docs, metadatas, distances):
            dist = float(distance or 0.0)
            similarity = max(0.0, 1.0 - dist)
            out.append(
                {
                    "issue_key": issue_key,
                    "text": text,
                    "metadata": metadata or {},
                    "distance": dist,
                    "similarity_score": similarity,
                }
            )
        return out

    def delete_all(self) -> None:
        """Delete all documents in the collection."""
        if self.count() == 0:
            return
        existing = self.collection.get(include=[])
        ids = existing.get("ids") or []
        if ids:
            self.collection.delete(ids=ids)


_VECTOR_STORE_SINGLETON: VectorStore | None = None
_VECTOR_STORE_LOCK = Lock()


def get_vector_store(settings=None) -> VectorStore:
    """Module-level singleton factory for vector store."""
    global _VECTOR_STORE_SINGLETON
    if _VECTOR_STORE_SINGLETON is not None:
        return _VECTOR_STORE_SINGLETON

    with _VECTOR_STORE_LOCK:
        if _VECTOR_STORE_SINGLETON is None:
            if settings is None:
                from app.core.config import get_settings

                settings = get_settings()
            _VECTOR_STORE_SINGLETON = VectorStore(db_path=settings.chroma_db_path)
        return _VECTOR_STORE_SINGLETON

