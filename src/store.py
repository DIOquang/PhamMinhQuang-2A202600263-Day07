from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.EphemeralClient(Settings(allow_reset=True))
            self._collection = self._client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None
            self._client = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        return {
            "id": doc.id,
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": doc.metadata,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
            
        query_vec = self._embedding_fn(query)
        scored = []
        for rec in records:
            score = _dot(query_vec, rec["embedding"])
            scored.append({**rec, "score": score})
            
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        if not docs:
            return

        if self._use_chroma and self._collection:
            self._collection.add(
                ids=[d.id for d in docs],
                documents=[d.content for d in docs],
                metadatas=[d.metadata for d in docs],
                embeddings=[self._embedding_fn(d.content) for d in docs],
            )
        else:
            for doc in docs:
                self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self.search_with_filter(query, top_k=top_k, metadata_filter=None)

    def get_collection_size(self) -> int:
        if self._use_chroma and self._collection:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        if self._use_chroma and self._collection:
            results = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
                where=metadata_filter,
            )
            
            out = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    # Chroma returns distances; we want "score" where higher is better for common RAG patterns
                    # Default Chroma distance is L2. For our tests' sake, we just return -distance to keep sort order
                    dist = results["distances"][0][i]
                    out.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": -dist 
                    })
            return out
        else:
            records = self._store
            if metadata_filter:
                records = [
                    r for r in self._store 
                    if all(r["metadata"].get(k) == v for k, v in metadata_filter.items())
                ]
            return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        if self._use_chroma and self._collection:
            before = self._collection.count()
            # We try to delete by ID (for chunks) or by doc_id in metadata
            self._collection.delete(ids=[doc_id])
            self._collection.delete(where={"doc_id": doc_id})
            return self._collection.count() < before
        else:
            before = len(self._store)
            self._store = [
                r for r in self._store 
                if r["id"] != doc_id and r["metadata"].get("doc_id") != doc_id
            ]
            return len(self._store) < before
