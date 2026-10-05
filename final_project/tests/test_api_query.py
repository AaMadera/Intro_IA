from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.config import Settings
from app.main import create_app
from app.schemas import Citation


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []

    def embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        self.calls.append((texts, task_type))
        return [[0.1, 0.2]]


class FakeStore:
    def __init__(self, citations: list[Citation]) -> None:
        self.citations = citations
        self.queries: list[tuple[list[float], int, str | None]] = []

    def count(self) -> int:
        return len(self.citations)

    def query(
        self, embedding: list[float], top_k: int, source: str | None = None
    ) -> list[Citation]:
        self.queries.append((embedding, top_k, source))
        return self.citations[:top_k]


class FakeGenerationClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[Citation]]] = []

    def answer(self, question: str, citations: list[Citation]) -> str:
        self.calls.append((question, citations))
        return "Respuesta basada en la evidencia [1]."


def make_client(
    tmp_path: Path,
    citations: list[Citation],
    min_score: float = 0.35,
) -> tuple[TestClient, FakeEmbeddingClient, FakeGenerationClient, FakeStore]:
    embedder = FakeEmbeddingClient()
    generator = FakeGenerationClient()
    store = FakeStore(citations)
    app = create_app(
        settings=Settings(chroma_path=tmp_path / "chroma", min_score=min_score),
        embedding_client=embedder,
        generation_client=generator,
        store=store,  # type: ignore[arg-type]
    )
    return TestClient(app), embedder, generator, store


def test_query_returns_generated_answer_and_retrieved_citations(tmp_path: Path) -> None:
    citation = Citation(
        id="chunk-1",
        source="manual.pdf",
        text="El chile habanero requiere un suelo bien drenado.",
        score=0.82,
        page=2,
        chunk_index=1,
    )
    client, embedder, generator, store = make_client(tmp_path, [citation])

    response = client.post(
        "/query",
        json={"question": "¿Qué suelo requiere?", "top_k": 3},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Respuesta basada en la evidencia [1].",
        "citations": [citation.__dict__],
        "abstained": False,
    }
    assert embedder.calls == [(["¿Qué suelo requiere?"], "RETRIEVAL_QUERY")]
    assert store.queries == [([0.1, 0.2], 3, None)]
    assert generator.calls == [("¿Qué suelo requiere?", [citation])]


def test_query_abstains_below_min_score_without_generation(tmp_path: Path) -> None:
    citation = Citation(
        id="chunk-1", source="manual.pdf", text="Evidencia lejana.", score=0.2
    )
    client, _, generator, _ = make_client(tmp_path, [citation])

    response = client.post("/query", json={"question": "Pregunta fuera de alcance"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "No tengo evidencia suficiente en los documentos indexados para responder esta pregunta.",
        "citations": [citation.__dict__],
        "abstained": True,
    }
    assert generator.calls == []


def test_query_empty_corpus_abstains_without_generation(tmp_path: Path) -> None:
    client, _, generator, _ = make_client(tmp_path, [])

    response = client.post("/query", json={"question": "¿Cómo se cultiva?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "No tengo evidencia suficiente en los documentos indexados para responder esta pregunta.",
        "citations": [],
        "abstained": True,
    }
    assert generator.calls == []


def test_query_rejects_whitespace_question(tmp_path: Path) -> None:
    client, _, _, _ = make_client(tmp_path, [])

    response = client.post("/query", json={"question": "   \n  "})

    assert response.status_code == 422
    assert "pregunta" in response.text.lower()


def test_query_rejects_unbounded_top_k(tmp_path: Path) -> None:
    client, _, _, _ = make_client(tmp_path, [])

    response = client.post("/query", json={"question": "Pregunta", "top_k": 0})

    assert response.status_code == 422


def test_query_accepts_request_level_min_score_and_top_k(tmp_path: Path) -> None:
    citation = Citation(id="chunk-1", source="manual.pdf", text="Evidencia", score=0.56)
    client, _, generator, store = make_client(tmp_path, [citation])

    response = client.post(
        "/query",
        json={"question": "Pregunta", "top_k": 7, "min_score": 0.55},
    )

    assert response.status_code == 200
    assert store.queries == [([0.1, 0.2], 7, None)]
    assert generator.calls


def test_query_uses_configured_defaults_when_overrides_are_omitted(
    tmp_path: Path,
) -> None:
    citations = [
        Citation(id="chunk-1", source="manual.pdf", text="Evidencia", score=0.36)
    ]
    client, _, generator, store = make_client(tmp_path, citations)

    response = client.post("/query", json={"question": "Pregunta"})

    assert response.status_code == 200
    assert store.queries == [([0.1, 0.2], 4, None)]


def test_query_forwards_source_filter(tmp_path: Path) -> None:
    citation = Citation(id="chunk-1", source="manual.pdf", text="Evidencia", score=0.8)
    client, _, _, store = make_client(tmp_path, [citation])

    response = client.post(
        "/query", json={"question": "Pregunta", "source": "manual.pdf"}
    )

    assert response.status_code == 200
    assert store.queries == [([0.1, 0.2], 4, "manual.pdf")]


@pytest.mark.parametrize("top_k", [1, 11])
def test_query_rejects_top_k_outside_phase_one_range(
    tmp_path: Path, top_k: int
) -> None:
    client, _, _, _ = make_client(tmp_path, [])

    assert (
        client.post("/query", json={"question": "Pregunta", "top_k": top_k}).status_code
        == 422
    )


@pytest.mark.parametrize("min_score", [0.05, 0.95, 0.36])
def test_query_rejects_invalid_min_score(tmp_path: Path, min_score: float) -> None:
    client, _, _, _ = make_client(tmp_path, [])

    assert (
        client.post(
            "/query", json={"question": "Pregunta", "min_score": min_score}
        ).status_code
        == 422
    )


def test_query_accepts_float_representation_of_valid_min_score(tmp_path: Path) -> None:
    client, _, _, _ = make_client(
        tmp_path,
        [Citation(id="chunk-1", source="manual.pdf", text="Evidencia", score=0.31)],
    )

    response = client.post(
        "/query", json={"question": "Pregunta", "min_score": 0.30000000000000004}
    )

    assert response.status_code == 200


def test_openapi_exposes_required_routes(tmp_path: Path) -> None:
    client, _, _, _ = make_client(tmp_path, [])

    routes = client.get("/openapi.json").json()["paths"]

    assert {"/health", "/ingest", "/query"} <= routes.keys()
