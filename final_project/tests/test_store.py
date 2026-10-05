from pathlib import Path

from app.schemas import ChunkRecord
from app.store import VectorStore


def test_store_uses_supplied_embeddings_and_returns_citations(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "chroma")
    chunks = [
        ChunkRecord(
            source="manual.pdf",
            text="El chile habanero requiere buen drenaje.",
            source_hash="abc123",
            chunk_index=0,
            page=2,
        ),
        ChunkRecord(
            source="agenda.pdf",
            text="La fertilización se ajusta al análisis del suelo.",
            source_hash="def456",
            chunk_index=1,
        ),
    ]
    embeddings = [[1.0, 0.0], [0.0, 1.0]]

    assert store.add_chunks(chunks, embeddings) == 2

    citations = store.query([1.0, 0.0], top_k=1)

    assert len(citations) == 1
    assert citations[0].source == "manual.pdf"
    assert citations[0].text == chunks[0].text
    assert citations[0].page == 2
    assert citations[0].chunk_index == 0
    assert citations[0].score == 1.0

    filtered = store.query([0.0, 1.0], top_k=2, source="agenda.pdf")
    assert len(filtered) == 1
    assert filtered[0].source == "agenda.pdf"


def test_store_persists_and_duplicate_ids_are_safe(tmp_path: Path) -> None:
    path = tmp_path / "chroma"
    chunk = ChunkRecord(
        source="manual.pdf",
        text="Contenido estable.",
        source_hash="same-source",
        chunk_index=0,
    )

    assert VectorStore(path).add_chunks([chunk], [[0.5, 0.5]]) == 1
    assert VectorStore(path).add_chunks([chunk], [[0.5, 0.5]]) == 0

    reopened = VectorStore(path)

    assert reopened.count() == 1
    assert reopened.query([0.5, 0.5], top_k=1)[0].text == chunk.text


def test_store_counts_chunks_for_source_and_hash(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "chroma")
    chunks = [
        ChunkRecord(
            source="manual.pdf", text="Uno", source_hash="hash-a", chunk_index=0
        ),
        ChunkRecord(
            source="manual.pdf", text="Dos", source_hash="hash-a", chunk_index=1
        ),
        ChunkRecord(
            source="manual.pdf", text="Tres", source_hash="hash-b", chunk_index=0
        ),
    ]

    assert store.add_chunks(chunks, [[1.0, 0.0]] * 3) == 3
    assert store.count_chunks_for_source("manual.pdf") == 3
    assert store.count_chunks_for_source("manual.pdf", "hash-a") == 2


def test_store_deletes_only_requested_source(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "chroma")
    chunks = [
        ChunkRecord(
            source="manual.pdf", text="Uno", source_hash="hash-a", chunk_index=0
        ),
        ChunkRecord(
            source="agenda.pdf", text="Dos", source_hash="hash-b", chunk_index=0
        ),
    ]
    store.add_chunks(chunks, [[1.0, 0.0], [0.0, 1.0]])

    assert store.delete_source("manual.pdf") == 1
    assert store.count_chunks_for_source("manual.pdf") == 0
    assert store.count_chunks_for_source("agenda.pdf") == 1
