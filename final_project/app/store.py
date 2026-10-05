from pathlib import Path
from typing import Any

import chromadb

from app.schemas import ChunkRecord, Citation


class VectorStore:
    def __init__(self, path: Path | str, collection_name: str = "habanero") -> None:
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=None,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: list[ChunkRecord],
        embeddings: list[list[float]],
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return 0

        ids = [chunk.stable_id for chunk in chunks]
        existing = set(self.collection.get(ids=ids, include=[]).get("ids", []))
        new_chunks = [
            (chunk, embedding)
            for chunk, embedding in zip(chunks, embeddings)
            if chunk.stable_id not in existing
        ]
        if not new_chunks:
            return 0

        self.collection.add(
            ids=[chunk.stable_id for chunk, _ in new_chunks],
            embeddings=[embedding for _, embedding in new_chunks],
            documents=[chunk.text for chunk, _ in new_chunks],
            metadatas=[self._metadata(chunk) for chunk, _ in new_chunks],
        )
        return len(new_chunks)

    def query(self, embedding: list[float], top_k: int) -> list[Citation]:
        if top_k <= 0:
            return []
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            self._citation(record_id, document, metadata, distance)
            for record_id, document, metadata, distance in zip(
                ids, documents, metadatas, distances
            )
        ]

    def count(self) -> int:
        return self.collection.count()

    @staticmethod
    def _metadata(chunk: ChunkRecord) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "source": chunk.source,
            "source_hash": chunk.source_hash,
            "chunk_index": chunk.chunk_index,
        }
        if chunk.page is not None:
            metadata["page"] = chunk.page
        if chunk.title is not None:
            metadata["title"] = chunk.title
        return metadata

    @staticmethod
    def _citation(
        record_id: str,
        document: str,
        metadata: dict[str, Any],
        distance: float,
    ) -> Citation:
        return Citation(
            id=record_id,
            source=str(metadata["source"]),
            text=document,
            score=max(0.0, 1.0 - float(distance)),
            page=metadata.get("page"),
            chunk_index=metadata.get("chunk_index"),
            title=metadata.get("title"),
        )
