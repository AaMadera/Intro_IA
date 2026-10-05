import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    google_api_key: str = field(default="", repr=False)
    google_embedding_model: str = "gemini-embedding-001"
    google_generation_model: str = "gemini-3.1-flash-lite"
    chroma_path: Path = Path("./chroma")
    chunk_size: int = 300
    chunk_overlap: int = 60
    top_k: int = 4
    min_score: float = 0.35
    model_retry_attempts: int = 5
    model_retry_backoff_seconds: float = 5.0
    embedding_batch_size: int = 32

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        settings = cls(
            google_api_key=os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY", ""),
            google_embedding_model=os.getenv(
                "GOOGLE_EMBEDDING_MODEL", cls.google_embedding_model
            ),
            google_generation_model=os.getenv(
                "GOOGLE_GENERATION_MODEL", cls.google_generation_model
            ),
            chroma_path=Path(os.getenv("CHROMA_PATH", str(cls.chroma_path))),
            chunk_size=int(os.getenv("CHUNK_SIZE", str(cls.chunk_size))),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", str(cls.chunk_overlap))),
            top_k=int(os.getenv("TOP_K", str(cls.top_k))),
            min_score=float(os.getenv("MIN_SCORE", str(cls.min_score))),
            model_retry_attempts=int(
                os.getenv("MODEL_RETRY_ATTEMPTS", str(cls.model_retry_attempts))
            ),
            model_retry_backoff_seconds=float(
                os.getenv(
                    "MODEL_RETRY_BACKOFF_SECONDS", str(cls.model_retry_backoff_seconds)
                )
            ),
            embedding_batch_size=int(
                os.getenv("EMBEDDING_BATCH_SIZE", str(cls.embedding_batch_size))
            ),
        )
        if (
            settings.chunk_size <= 0
            or not 0 <= settings.chunk_overlap < settings.chunk_size
        ):
            raise ValueError("CHUNK_OVERLAP must satisfy 0 <= overlap < CHUNK_SIZE")
        if (
            settings.model_retry_attempts < 1
            or settings.model_retry_backoff_seconds < 0
            or settings.embedding_batch_size < 1
        ):
            raise ValueError(
                "Model retry settings must be non-negative and attempts >= 1"
            )
        return settings


def get_settings() -> Settings:
    return Settings.from_env()
