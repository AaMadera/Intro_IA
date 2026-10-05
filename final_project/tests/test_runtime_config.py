from pathlib import Path

import yaml

from app.config import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_settings_accepts_legacy_gemini_api_key_name(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    settings = Settings.from_env()

    assert settings.google_api_key == "test-key"


def test_generation_model_defaults_to_gemini_25_flash(monkeypatch) -> None:
    monkeypatch.setattr("app.config.load_dotenv", lambda: None)
    monkeypatch.delenv("GOOGLE_GENERATION_MODEL", raising=False)

    settings = Settings.from_env()

    assert settings.google_generation_model == "gemini-3.1-flash-lite"


def test_generation_model_can_be_overridden(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_GENERATION_MODEL", "otro-modelo-compatible")

    settings = Settings.from_env()

    assert settings.google_generation_model == "otro-modelo-compatible"


def load_compose() -> dict:
    compose_path = PROJECT_ROOT / "docker-compose.yml"
    assert compose_path.is_file()
    return yaml.safe_load(compose_path.read_text(encoding="utf-8"))


def test_compose_defines_api_and_ui_runtime_contract() -> None:
    compose = load_compose()
    services = compose["services"]

    assert set(services) == {"api", "ui"}
    assert services["api"]["ports"] == ["8000:8000"]
    assert services["ui"]["ports"] == ["8501:8501"]
    assert services["api"]["command"] == [
        "uv",
        "run",
        "--locked",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    assert services["ui"]["command"] == [
        "uv",
        "run",
        "--locked",
        "streamlit",
        "run",
        "ui/streamlit_app.py",
        "--server.address",
        "0.0.0.0",
        "--server.port",
        "8501",
    ]


def test_compose_wires_secret_and_persistent_runtime_paths() -> None:
    compose_text = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    compose = load_compose()
    api = compose["services"]["api"]

    assert api["environment"]["GOOGLE_API_KEY"] == (
        "${GOOGLE_API_KEY:-${GEMINI_API_KEY:?GOOGLE_API_KEY o GEMINI_API_KEY debe estar "
        "configurada en final_project/.env}}"
    )
    assert "GOOGLE_API_KEY=" not in compose_text
    assert (
        api["environment"]["GOOGLE_GENERATION_MODEL"]
        == "${GOOGLE_GENERATION_MODEL:-gemini-3.1-flash-lite}"
    )
    assert "./chroma:/app/chroma" in api["volumes"]
    assert "./data/processed:/app/data/processed" in api["volumes"]
    assert "./data/source:/app/data/source" in api["volumes"]
    assert "./pdfs_seed:/app/pdfs_seed:ro" in api["volumes"]


def test_compose_has_api_healthcheck_and_fallback_documentation() -> None:
    compose = load_compose()
    api = compose["services"]["api"]

    healthcheck = api["healthcheck"]
    assert healthcheck["test"] == [
        "CMD",
        "python",
        "-c",
        "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')",
    ]
    assert healthcheck["interval"]
    assert healthcheck["timeout"]
    assert healthcheck["retries"]

    dockerfile = (PROJECT_ROOT / "Dockerfile.api").read_text(encoding="utf-8")
    assert "opendataloader" in dockerfile.lower()
    assert "pypdf" in dockerfile.lower() or "fallback" in dockerfile.lower()
