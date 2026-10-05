from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_reports_api_and_chroma_without_exposing_secrets(tmp_path: Path) -> None:
    app = create_app(
        settings=Settings(
            google_api_key="secret-value", chroma_path=tmp_path / "chroma"
        )
    )

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"api": "ok", "chroma": "ok"}
    assert "secret-value" not in response.text
