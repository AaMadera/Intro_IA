import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.config import Settings
from app.main import create_app


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []

    def embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        self.calls.append((texts, task_type))
        return [[float(index), 1.0] for index, _ in enumerate(texts, start=1)]


class FailingBatchEmbeddingClient(FakeEmbeddingClient):
    def __init__(self) -> None:
        super().__init__()
        self.fail_on_call: int | None = 2

    def embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        self.calls.append((texts, task_type))
        if self.fail_on_call is not None and len(self.calls) == self.fail_on_call:
            from app.retry import RetryExhaustedError

            raise RetryExhaustedError(
                "El servicio de embeddings", 5, RuntimeError("429")
            )
        return [[float(index), 1.0] for index, _ in enumerate(texts, start=1)]


def make_client(tmp_path: Path, fake: FakeEmbeddingClient | None = None) -> TestClient:
    return TestClient(
        create_app(
            settings=Settings(
                chroma_path=tmp_path / "chroma",
                chunk_size=4,
                chunk_overlap=1,
            ),
            embedding_client=fake or FakeEmbeddingClient(),
            processed_dir=tmp_path / "processed",
        )
    )


def make_pdf(text: str = "Cultivo") -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): writer._add_object(font)}
            )
        }
    )
    content = DecodedStreamObject()
    content.set_data(f"BT /F1 12 Tf 20 100 Td ({text}) Tj ET".encode())
    page[NameObject("/Contents")] = writer._add_object(content)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_ingest_extracts_pdf_and_creates_processed_output(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/ingest",
        files={"files": ("manual.pdf", make_pdf(), "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["documents"] == 1
    assert response.json()["chunks"] == 1
    assert list((tmp_path / "processed").glob("*.txt"))


def test_ingest_uploads_supported_files_and_is_idempotent(tmp_path: Path) -> None:
    fake = FakeEmbeddingClient()
    client = make_client(tmp_path, fake)
    files = [
        (
            "files",
            ("nota.md", b"Cultivo de chile habanero en Yucatan.", "text/markdown"),
        ),
        ("files", ("datos.txt", b"La fertilizacion depende del suelo.", "text/plain")),
    ]

    first = client.post("/ingest", files=files)
    second = client.post("/ingest", files=files)

    assert first.status_code == 200
    assert first.json()["documents"] == 2
    assert first.json()["chunks"] > 0
    assert first.json()["errors"] == []
    assert second.status_code == 200
    assert second.json()["documents"] == 2
    assert second.json()["chunks"] == 0
    assert len(fake.calls) == 2
    assert all(task_type == "RETRIEVAL_DOCUMENT" for _, task_type in fake.calls)


def test_ingest_resumes_after_embedding_quota_failure(tmp_path: Path) -> None:
    fake = FailingBatchEmbeddingClient()
    client = TestClient(
        create_app(
            settings=Settings(
                chroma_path=tmp_path / "chroma",
                chunk_size=2,
                chunk_overlap=0,
                embedding_batch_size=1,
            ),
            embedding_client=fake,
            processed_dir=tmp_path / "processed",
        )
    )
    first = client.post(
        "/ingest",
        files={
            "files": ("partial.txt", b"uno dos tres cuatro cinco seis", "text/plain")
        },
    )

    assert first.json()["chunks"] == 1
    assert "espere unos minutos" in first.json()["errors"][0]["message"]

    fake.fail_on_call = None
    second = client.post(
        "/ingest",
        files={
            "files": ("partial.txt", b"uno dos tres cuatro cinco seis", "text/plain")
        },
    )

    assert second.json()["chunks"] == 2
    assert len(fake.calls) == 4
    assert [call[0] for call in fake.calls] == [
        ["uno dos"],
        ["tres cuatro"],
        ["tres cuatro"],
        ["cinco seis"],
    ]


def test_ingest_skips_extraction_for_completed_same_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import importlib

    fake = FakeEmbeddingClient()
    client = make_client(tmp_path, fake)
    files = {"files": ("complete.txt", b"Contenido completo.", "text/plain")}
    first = client.post("/ingest", files=files)
    assert first.json()["chunks"] == 1

    main_module = importlib.import_module("app.main")

    def extraction_must_not_run(*args: object, **kwargs: object) -> object:
        raise AssertionError("la extracción no debe repetirse")

    monkeypatch.setattr(main_module, "extract_document", extraction_must_not_run)
    second = client.post("/ingest", files=files)

    assert second.json()["documents"] == 1
    assert second.json()["chunks"] == 0


def test_reindex_uploaded_document_uses_cached_extraction(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    files = {"files": ("uploaded.txt", b"Texto para reindexar.", "text/plain")}
    first = client.post("/ingest", files=files)
    assert first.json()["chunks"] == 1
    client.delete("/documents/uploaded.txt")

    response = client.post("/documents/uploaded.txt/reindex")

    assert response.status_code == 200
    assert response.json() == {"documents": 1, "chunks": 1, "errors": []}


def test_ingest_reports_empty_and_unsupported_files_in_spanish(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post(
        "/ingest",
        files=[
            ("files", ("vacio.txt", b"   ", "text/plain")),
            ("files", ("imagen.csv", b"a,b", "text/csv")),
        ],
    )

    assert response.status_code == 200
    errors = response.json()["errors"]
    assert len(errors) == 2
    assert all(error["file"] in {"vacio.txt", "imagen.csv"} for error in errors)
    assert all(error["message"] for error in errors)
    assert any("vacío" in error["message"].lower() for error in errors)
    assert any("soport" in error["message"].lower() for error in errors)


def test_ingest_indexes_the_bundled_corpus_path(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    for index in range(4):
        (corpus / f"documento-{index}.txt").write_text(
            f"Contenido del documento {index} sobre chile habanero.", encoding="utf-8"
        )
    app = create_app(
        settings=Settings(
            chroma_path=tmp_path / "chroma", chunk_size=20, chunk_overlap=0
        ),
        embedding_client=FakeEmbeddingClient(),
        corpus_dir=corpus,
    )

    response = TestClient(app).post("/ingest", data={"action": "corpus"})

    assert response.status_code == 200
    assert response.json()["documents"] == 4
    assert response.json()["chunks"] == 4
    assert response.json()["errors"] == []


def test_ingest_rejects_corpus_path_outside_configured_directory(
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("Contenido fuera del corpus.", encoding="utf-8")
    app = create_app(
        settings=Settings(chroma_path=tmp_path / "chroma"),
        embedding_client=FakeEmbeddingClient(),
        corpus_dir=corpus,
    )

    response = TestClient(app).post(
        "/ingest",
        data={"action": "corpus", "path": str(outside)},
    )

    assert response.status_code == 400
    assert "directorio configurado" in response.json()["detail"]


def test_ingest_reports_missing_api_key_without_a_client(tmp_path: Path) -> None:
    app = create_app(settings=Settings(chroma_path=tmp_path / "chroma"))

    response = TestClient(app).post(
        "/ingest",
        files={"files": ("nota.txt", b"Contenido valido.", "text/plain")},
    )

    assert response.status_code == 503
    assert "GOOGLE_API_KEY" not in response.text
    assert "clave" in response.json()["detail"].lower()
