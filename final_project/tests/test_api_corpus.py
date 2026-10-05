from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.corpus import EXPECTED_CORPUS_FILES
from app.main import create_app

from tests.test_api_ingest import FakeEmbeddingClient, make_pdf


def make_corpus(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    return corpus


def make_client(tmp_path: Path, corpus: Path) -> TestClient:
    return TestClient(
        create_app(
            settings=Settings(
                chroma_path=tmp_path / "chroma", chunk_size=20, chunk_overlap=0
            ),
            embedding_client=FakeEmbeddingClient(),
            corpus_dir=corpus,
            processed_dir=tmp_path / "processed",
        )
    )


def test_corpus_status_represents_exactly_four_seed_pdfs(tmp_path: Path) -> None:
    corpus = make_corpus(tmp_path)
    for index, filename in enumerate(EXPECTED_CORPUS_FILES):
        (corpus / filename).write_bytes(make_pdf(f"Cultivo {index}"))
    (corpus / EXPECTED_CORPUS_FILES[-1]).unlink()
    client = make_client(tmp_path, corpus)

    response = client.get("/corpus/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["expected"] == 4
    assert len(payload["files"]) == 4
    assert payload["counts"]["missing"] == 1


def test_corpus_ingestion_updates_success_and_duplicate_status(tmp_path: Path) -> None:
    corpus = make_corpus(tmp_path)
    for index, filename in enumerate(EXPECTED_CORPUS_FILES):
        (corpus / filename).write_bytes(make_pdf(f"Cultivo {index}"))
    client = make_client(tmp_path, corpus)

    first = client.post("/ingest", data={"action": "corpus"})
    second = client.post("/ingest", data={"action": "corpus"})
    status = client.get("/corpus/status").json()

    assert first.json()["documents"] == 4
    assert second.json()["chunks"] == 0
    assert len(client.app.state.embedding_client.calls) == 4
    assert status["loaded"] == 4
    assert all(file["chunks"] > 0 for file in status["files"])


def test_corpus_ingestion_records_failed_pdf(tmp_path: Path) -> None:
    corpus = make_corpus(tmp_path)
    for index, filename in enumerate(EXPECTED_CORPUS_FILES):
        (corpus / filename).write_bytes(make_pdf(f"Cultivo {index}"))
    (corpus / EXPECTED_CORPUS_FILES[0]).write_bytes(b"not a pdf")
    client = make_client(tmp_path, corpus)

    response = client.post("/ingest", data={"action": "corpus"})
    status = client.get("/corpus/status").json()

    assert response.status_code == 200
    failed = next(
        file for file in status["files"] if file["file"] == EXPECTED_CORPUS_FILES[0]
    )
    assert failed["status"] == "failed"
    assert failed["error"]


def test_uploaded_files_are_not_in_seed_status(tmp_path: Path) -> None:
    corpus = make_corpus(tmp_path)
    client = make_client(tmp_path, corpus)

    response = client.post(
        "/ingest", files={"files": ("uploaded.txt", b"Contenido", "text/plain")}
    )

    assert response.status_code == 200
    assert all(
        file["file"] in EXPECTED_CORPUS_FILES
        for file in client.get("/corpus/status").json()["files"]
    )


def test_delete_document_removes_only_requested_source(tmp_path: Path) -> None:
    corpus = make_corpus(tmp_path)
    for index, filename in enumerate(EXPECTED_CORPUS_FILES):
        (corpus / filename).write_bytes(make_pdf(f"Cultivo {index}"))
    client = make_client(tmp_path, corpus)
    client.post("/ingest", data={"action": "corpus"})

    response = client.delete(f"/documents/{EXPECTED_CORPUS_FILES[0]}")

    assert response.status_code == 200
    assert response.json()["deleted_chunks"] > 0
    assert client.app.state.store.count_chunks_for_source(EXPECTED_CORPUS_FILES[0]) == 0
    assert client.app.state.store.count() > 0


def test_reindex_document_rebuilds_only_requested_source(tmp_path: Path) -> None:
    corpus = make_corpus(tmp_path)
    for index, filename in enumerate(EXPECTED_CORPUS_FILES):
        (corpus / filename).write_bytes(make_pdf(f"Cultivo {index}"))
    client = make_client(tmp_path, corpus)
    filename = EXPECTED_CORPUS_FILES[0]
    client.post("/ingest", data={"action": "corpus", "path": str(corpus / filename)})
    client.delete(f"/documents/{filename}")

    response = client.post(f"/documents/{filename}/reindex")

    assert response.status_code == 200
    assert response.json()["documents"] == 1
    assert response.json()["chunks"] > 0
