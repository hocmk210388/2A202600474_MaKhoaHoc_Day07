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
        self._client = None
        self._next_index = 0

        try:
            import chromadb

            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None
            self._client = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        rid = str(self._next_index)
        self._next_index += 1
        emb = self._embedding_fn(doc.content)
        metadata = {**doc.metadata, "doc_id": doc.id}
        return {
            "id": rid,
            "content": doc.content,
            "embedding": emb,
            "metadata": metadata,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records or top_k <= 0:
            return []
        q_emb = self._embedding_fn(query)
        ranked: list[tuple[float, dict[str, Any]]] = []
        for rec in records:
            score = _dot(q_emb, rec["embedding"])
            ranked.append((score, rec))
        ranked.sort(key=lambda x: x[0], reverse=True)
        out: list[dict[str, Any]] = []
        for score, rec in ranked[:top_k]:
            out.append(
                {
                    "content": rec["content"],
                    "score": score,
                    "metadata": rec["metadata"],
                }
            )
        return out

    def add_documents(self, docs: list[Document]) -> None:
        for doc in docs:
            rec = self._make_record(doc)
            if self._use_chroma and self._collection is not None:
                self._collection.add(
                    ids=[rec["id"]],
                    embeddings=[rec["embedding"]],
                    documents=[rec["content"]],
                    metadatas=[rec["metadata"]],
                )
            else:
                self._store.append(rec)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self._use_chroma and self._collection is not None:
            n = self.get_collection_size()
            if n == 0:
                return []
            q_emb = self._embedding_fn(query)
            res = self._collection.query(
                query_embeddings=[q_emb],
                n_results=min(top_k, n),
                include=["documents", "metadatas", "distances"],
            )
            rows: list[dict[str, Any]] = []
            docs_list = res.get("documents") or [[]]
            metas_list = res.get("metadatas") or [[]]
            dists_list = res.get("distances") or [[]]
            for i in range(len(docs_list[0])):
                dist = dists_list[0][i] if dists_list and dists_list[0] else 0.0
                score = 1.0 - float(dist)
                rows.append(
                    {
                        "content": docs_list[0][i],
                        "score": score,
                        "metadata": metas_list[0][i] if metas_list and metas_list[0] else {},
                    }
                )
            rows.sort(key=lambda r: r["score"], reverse=True)
            return rows[:top_k]
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        if self._use_chroma and self._collection is not None:
            return int(self._collection.count())
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict | None = None
    ) -> list[dict[str, Any]]:
        if self._use_chroma and self._collection is not None:
            n = self.get_collection_size()
            if n == 0:
                return []
            q_emb = self._embedding_fn(query)
            where: dict[str, Any] | None = None
            if metadata_filter:
                clauses = [{k: v} for k, v in metadata_filter.items()]
                where = clauses[0] if len(clauses) == 1 else {"$and": clauses}
            res = self._collection.query(
                query_embeddings=[q_emb],
                n_results=min(top_k, n),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            rows: list[dict[str, Any]] = []
            docs_list = res.get("documents") or [[]]
            metas_list = res.get("metadatas") or [[]]
            dists_list = res.get("distances") or [[]]
            for i in range(len(docs_list[0])):
                dist = dists_list[0][i] if dists_list and dists_list[0] else 0.0
                score = 1.0 - float(dist)
                rows.append(
                    {
                        "content": docs_list[0][i],
                        "score": score,
                        "metadata": metas_list[0][i] if metas_list and metas_list[0] else {},
                    }
                )
            rows.sort(key=lambda r: r["score"], reverse=True)
            return rows[:top_k]

        pool = self._store
        if metadata_filter:
            pool = [
                r
                for r in self._store
                if all(r["metadata"].get(k) == v for k, v in metadata_filter.items())
            ]
        return self._search_records(query, pool, top_k)

    def delete_document(self, doc_id: str) -> bool:
        if self._use_chroma and self._collection is not None:
            got = self._collection.get(where={"doc_id": doc_id})
            ids = got.get("ids") or []
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True
        before = len(self._store)
        self._store = [r for r in self._store if r["metadata"].get("doc_id") != doc_id]
        return len(self._store) < before
