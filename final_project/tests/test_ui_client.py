import importlib
from pathlib import Path

import httpx
import pytest


@pytest.fixture
def ui_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("API_BASE_URL", "http://api.test:9000/")
    return importlib.import_module("ui.streamlit_app")


def test_api_base_url_is_configurable(ui_client) -> None:
    assert ui_client.get_api_base_url() == "http://api.test:9000"


def test_index_corpus_decodes_successful_response(
    ui_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        calls.append({"url": url, **kwargs})
        return httpx.Response(
            200,
            json={"documents": 4, "chunks": 12, "errors": []},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(ui_client.httpx, "post", fake_post)

    result = ui_client.index_corpus()

    assert result == {"documents": 4, "chunks": 12, "errors": []}
    assert calls[0]["url"] == "http://api.test:9000/ingest"
    assert calls[0]["data"] == {"action": "corpus"}


def test_query_decodes_answer_and_citations(
    ui_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = {
        "answer": "Requiere suelo bien drenado [1].",
        "citations": [
            {
                "id": "chunk-1",
                "source": "manual.pdf",
                "text": "El suelo debe drenar bien.",
                "score": 0.82,
                "page": 2,
            }
        ],
        "abstained": False,
    }

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        assert url == "http://api.test:9000/query"
        assert kwargs["json"] == {"question": "¿Qué suelo requiere?", "top_k": 4}
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(ui_client.httpx, "post", fake_post)

    assert ui_client.ask_question("¿Qué suelo requiere?", top_k=4) == payload


def test_http_failure_becomes_spanish_client_error(
    ui_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(ui_client.httpx, "post", fake_post)

    with pytest.raises(ui_client.UIClientError, match="API no disponible"):
        ui_client.index_corpus()


def test_malformed_response_becomes_spanish_client_error(
    ui_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            200, json={"unexpected": True}, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(ui_client.httpx, "post", fake_post)

    with pytest.raises(ui_client.UIClientError, match="respuesta inválida"):
        ui_client.index_corpus()


def test_ui_source_does_not_import_backend_providers() -> None:
    source = Path(__file__).parents[1].joinpath("ui", "streamlit_app.py").read_text()

    assert "chromadb" not in source
    assert "google.genai" not in source
